import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.intent_parser import TaskIntent, parse_transcript
from backend.voice_pipeline import transcribe_audio
from backend.websocket_manager import WebSocketManager
from backend.browser_automation import BrowserAutomation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

manager = WebSocketManager()
browser = BrowserAutomation()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing browser automation")
    try:
        await browser.initialize()
    except Exception as exc:
        logger.warning("Browser automation unavailable at startup: %s", exc)
    yield
    logger.info("Shutting down — cleaning up browser resources")
    await browser.cleanup()


app = FastAPI(title="Voice Browser Agent", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    transcript: str


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "browser_sessions": browser.get_session_count(),
        "ws_connections": manager.get_connection_count(),
    }


# ---------------------------------------------------------------------------
# Intent parsing
# ---------------------------------------------------------------------------

@app.post("/parse", response_model=TaskIntent, summary="Parse a text transcript into a TaskIntent")
async def parse_text(request: ParseRequest):
    """
    Accept a plain-text voice transcript and return a validated TaskIntent JSON.

    - **action_type**: primary browser action
    - **reversibility**: read | reversible | irreversible
    - **requires_confirmation**: true for all irreversible actions (HITL gate)
    - **ambiguity_flags**: non-empty when the command is unclear
    """
    if not request.transcript.strip():
        raise HTTPException(status_code=422, detail="transcript must not be empty")
    try:
        return await parse_transcript(request.transcript)
    except Exception as exc:
        logger.exception("Intent parsing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post(
    "/parse/audio",
    response_model=TaskIntent,
    summary="Transcribe audio via Whisper then parse into a TaskIntent",
)
async def parse_audio(audio: UploadFile = File(...)):
    """
    Accept a WAV/MP3/M4A/OGG audio file, transcribe with Whisper-1, then parse intent.
    """
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=422, detail="audio file is empty")
    try:
        transcript = await transcribe_audio(audio_bytes, filename=audio.filename or "audio.wav")
        intent = await parse_transcript(transcript)
        intent.raw_transcript = transcript
        return intent
    except Exception as exc:
        logger.exception("Audio transcription or parsing failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# WebSocket — browser automation control channel
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                message = json.loads(raw)
            except json.JSONDecodeError:
                await manager.send_message(websocket, {"type": "error", "error": "Invalid JSON"})
                continue

            msg_type = message.get("type")

            if msg_type == "connect-browser":
                try:
                    url = message.get("url", "https://www.google.com")
                    session_id = await browser.create_session(url)
                    await manager.send_message(websocket, {
                        "type": "browser-status",
                        "connected": True,
                        "sessionId": session_id,
                        "url": url,
                    })
                except Exception as exc:
                    logger.exception("Failed to create browser session")
                    await manager.send_message(websocket, {
                        "type": "browser-status",
                        "connected": False,
                        "error": str(exc),
                    })

            elif msg_type == "disconnect-browser":
                try:
                    session_id = message.get("sessionId")
                    if session_id:
                        await browser.close_session(session_id)
                    await manager.send_message(websocket, {
                        "type": "browser-status",
                        "connected": False,
                    })
                except Exception as exc:
                    await manager.send_message(websocket, {"type": "error", "error": str(exc)})

            elif msg_type == "execute-command":
                try:
                    result = await browser.execute_command(
                        message.get("sessionId"), message.get("command", {})
                    )
                    await manager.send_message(websocket, {
                        "type": "command-result",
                        "success": True,
                        "result": result,
                    })
                except Exception as exc:
                    await manager.send_message(websocket, {
                        "type": "command-result",
                        "success": False,
                        "error": str(exc),
                    })

            elif msg_type == "take-screenshot":
                try:
                    screenshot_b64 = await browser.take_screenshot(message.get("sessionId"))
                    await manager.send_message(websocket, {
                        "type": "screenshot-result",
                        "success": True,
                        "screenshot": screenshot_b64,
                        "timestamp": datetime.now().isoformat(),
                    })
                except Exception as exc:
                    await manager.send_message(websocket, {
                        "type": "screenshot-result",
                        "success": False,
                        "error": str(exc),
                    })

            else:
                await manager.send_message(websocket, {
                    "type": "error",
                    "error": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        logger.exception("Unexpected WebSocket error")
        manager.disconnect(websocket)
