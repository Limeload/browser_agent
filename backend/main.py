"""
Voice Browser Agent — FastAPI backend.

Endpoints
---------
GET  /health              server + session stats
POST /parse               text transcript → TaskIntent (Claude)
POST /parse/audio         audio file → Whisper → TaskIntent
WS   /ws                  browser automation channel

WebSocket message types (client → server)
------------------------------------------
connect-browser     { url }
disconnect-browser  { sessionId }
execute-command     { sessionId, command }   command = VoiceCommand / TaskIntent dict
take-screenshot     { sessionId }
approve-action      { actionId, modifiedIntent? }
deny-action         { actionId }

WebSocket message types (server → client)
------------------------------------------
browser-status      { connected, sessionId?, url?, error? }
command-result      { success, result?, error? }
screenshot-result   { success, screenshot?, timestamp?, error? }
action-pending      { actionId, actionType, reversibility, description, target? }
action-denied       { actionId, reason? }
injection-blocked   { text, detections }
error               { error }
"""

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.browser_automation import BrowserAutomation
from backend.database import close as db_close
from backend.guard_layer import scan_and_log
from backend.hitl_queue import HITLQueue
from backend.intent_parser import TaskIntent, parse_transcript
from backend.voice_pipeline import transcribe_audio
from backend.websocket_manager import WebSocketManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

browser = BrowserAutomation()
manager = WebSocketManager()
hitl = HITLQueue()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing browser automation")
    try:
        await browser.initialize()
    except Exception as exc:
        logger.warning("Browser unavailable at startup: %s", exc)
    yield
    hitl.cancel_all()
    await browser.cleanup()
    await db_close()


app = FastAPI(title="Voice Browser Agent", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.2.0",
        "browser_sessions": browser.get_session_count(),
        "ws_connections": manager.get_connection_count(),
        "hitl_pending": len(hitl.list_pending()),
    }


class ParseRequest(BaseModel):
    transcript: str


@app.post("/parse", response_model=TaskIntent)
async def parse_text(request: ParseRequest):
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="transcript must not be empty")
    try:
        return await parse_transcript(request.transcript)
    except Exception as exc:
        logger.exception("Intent parsing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/parse/audio", response_model=TaskIntent)
async def parse_audio(audio: UploadFile = File(...)):
    data = await audio.read()
    if not data:
        raise HTTPException(status_code=422, detail="audio file is empty")
    try:
        transcript = await transcribe_audio(data, filename=audio.filename or "audio.wav")
        intent = await parse_transcript(transcript)
        intent.raw_transcript = transcript
        return intent
    except Exception as exc:
        logger.exception("Audio parse failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# WebSocket — browser automation channel
# ---------------------------------------------------------------------------


async def _execute_after_approval(
    ws: WebSocket,
    session_id: str,
    action_id: str,
    future: asyncio.Future,
) -> None:
    """Background task: wait for HITL resolution then run the command."""
    try:
        resolved_command = await asyncio.wait_for(asyncio.shield(future), timeout=300)
    except asyncio.TimeoutError:
        hitl.cancel(action_id)
        await manager.send_message(ws, {
            "type": "action-denied",
            "actionId": action_id,
            "reason": "Approval timed out (5 min)",
        })
        return

    if resolved_command is None:
        await manager.send_message(ws, {"type": "action-denied", "actionId": action_id})
        return

    try:
        result = await browser.execute_command(session_id, resolved_command)
        await manager.send_message(ws, {
            "type": "command-result", "success": True, "result": result
        })
    except Exception as exc:
        await manager.send_message(ws, {
            "type": "command-result", "success": False, "error": str(exc)
        })


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_message(websocket, {"type": "error", "error": "Invalid JSON"})
                continue

            t = msg.get("type")

            # ------------------------------------------------------------------
            if t == "connect-browser":
                try:
                    url = msg.get("url", "https://www.google.com")
                    sid = await browser.create_session(url)
                    await manager.send_message(websocket, {
                        "type": "browser-status",
                        "connected": True,
                        "sessionId": sid,
                        "url": url,
                    })
                except Exception as exc:
                    logger.exception("create_session failed")
                    await manager.send_message(websocket, {
                        "type": "browser-status", "connected": False, "error": str(exc)
                    })

            # ------------------------------------------------------------------
            elif t == "disconnect-browser":
                try:
                    sid = msg.get("sessionId")
                    if sid:
                        await browser.close_session(sid)
                    await manager.send_message(websocket, {
                        "type": "browser-status", "connected": False
                    })
                except Exception as exc:
                    await manager.send_message(websocket, {"type": "error", "error": str(exc)})

            # ------------------------------------------------------------------
            elif t == "execute-command":
                command: dict = msg.get("command", {})
                sid = msg.get("sessionId", "")
                page_url = ""

                # 1. GuardLayer: scan command text for injection
                text_to_scan = " ".join(filter(None, [
                    command.get("raw_transcript", ""),
                    command.get("description", ""),
                    command.get("target", ""),
                    command.get("value", ""),
                ]))
                if text_to_scan:
                    detections = await scan_and_log(text_to_scan, page_url=page_url)
                    if detections:
                        await manager.send_message(websocket, {
                            "type": "injection-blocked",
                            "text": text_to_scan[:200],
                            "detections": [
                                {"attack_type": d.attack_type, "confidence": d.confidence}
                                for d in detections
                            ],
                        })
                        continue  # drop the command

                # 2. HITL gate: pause irreversible actions for human approval
                needs_approval = (
                    command.get("requires_confirmation")
                    or command.get("reversibility") == "irreversible"
                )
                if needs_approval:
                    future: asyncio.Future = asyncio.get_event_loop().create_future()
                    action_id = hitl.register(command, future)
                    await manager.send_message(websocket, {
                        "type": "action-pending",
                        "actionId": action_id,
                        "actionType": command.get("action_type") or command.get("command"),
                        "reversibility": command.get("reversibility", "irreversible"),
                        "description": command.get("description", ""),
                        "target": command.get("target"),
                    })
                    asyncio.create_task(
                        _execute_after_approval(websocket, sid, action_id, future)
                    )
                    continue  # loop keeps processing (for approve/deny messages)

                # 3. Execute immediately
                try:
                    result = await browser.execute_command(sid, command)
                    await manager.send_message(websocket, {
                        "type": "command-result", "success": True, "result": result
                    })
                except Exception as exc:
                    await manager.send_message(websocket, {
                        "type": "command-result", "success": False, "error": str(exc)
                    })

            # ------------------------------------------------------------------
            elif t == "approve-action":
                action_id = msg.get("actionId", "")
                modified = msg.get("modifiedIntent")
                if not hitl.resolve(action_id, "approved", modified):
                    await manager.send_message(websocket, {
                        "type": "error", "error": f"Unknown actionId: {action_id}"
                    })

            # ------------------------------------------------------------------
            elif t == "deny-action":
                action_id = msg.get("actionId", "")
                if not hitl.resolve(action_id, "denied"):
                    await manager.send_message(websocket, {
                        "type": "error", "error": f"Unknown actionId: {action_id}"
                    })

            # ------------------------------------------------------------------
            elif t == "take-screenshot":
                try:
                    sid = msg.get("sessionId")
                    b64 = await browser.take_screenshot(sid)
                    await manager.send_message(websocket, {
                        "type": "screenshot-result",
                        "success": True,
                        "screenshot": b64,
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception as exc:
                    await manager.send_message(websocket, {
                        "type": "screenshot-result", "success": False, "error": str(exc)
                    })

            # ------------------------------------------------------------------
            else:
                await manager.send_message(websocket, {
                    "type": "error", "error": f"Unknown message type: {t}"
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        logger.exception("Unexpected WebSocket error")
        manager.disconnect(websocket)
