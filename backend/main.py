from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
from typing import Dict, Any
from datetime import datetime
import logging
from contextlib import asynccontextmanager

from .models import BrowserSession
from .browser_automation import BrowserAutomation
from .websocket_manager import WebSocketManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
browser_automation = BrowserAutomation()
websocket_manager = WebSocketManager()
active_sessions: Dict[str, BrowserSession] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Voice Browser Agent backend...")
    await browser_automation.initialize()
    yield
    # Shutdown
    logger.info("Shutting down Voice Browser Agent backend...")
    await browser_automation.cleanup()
    await websocket_manager.disconnect_all()

app = FastAPI(
    title="Voice Browser Agent API",
    description="Sophisticated voice-enabled browser automation agent",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (React build)
app.mount("/static", StaticFiles(directory="dist"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the React application"""
    try:
        with open("dist/index.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Voice Browser Agent</h1><p>Please build the React frontend first.</p>")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_sessions": len(active_sessions),
        "timestamp": datetime.now().isoformat(),
        "browser_automation": "available"
    }

@app.get("/api/sessions")
async def get_sessions():
    """Get all active sessions"""
    sessions = []
    for session_id, session in active_sessions.items():
        sessions.append({
            "session_id": session_id,
            "url": session.url,
            "connected": session.connected,
            "created_at": session.created_at.isoformat()
        })
    
    return {
        "sessions": sessions,
        "count": len(sessions)
    }

@app.delete("/api/sessions/{session_id}")
async def close_session(session_id: str):
    """Close a specific session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    try:
        await browser_automation.close_session(session_id)
        del active_sessions[session_id]
        return {"success": True, "message": "Session closed successfully"}
    except Exception as e:
        logger.error(f"Failed to close session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to close session: {str(e)}")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket_manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_websocket_message(websocket, message)
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket)

async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any]):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    try:
        if message_type == "connect-browser":
            await handle_connect_browser(websocket, message)
        elif message_type == "disconnect-browser":
            await handle_disconnect_browser(websocket, message)
        elif message_type == "execute-command":
            await handle_execute_command(websocket, message)
        elif message_type == "take-screenshot":
            await handle_take_screenshot(websocket, message)
        else:
            await websocket_manager.send_message(websocket, {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            })
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await websocket_manager.send_message(websocket, {
            "type": "error",
            "message": str(e)
        })

async def handle_connect_browser(websocket: WebSocket, message: Dict[str, Any]):
    """Handle browser connection request"""
    url = message.get("url", "https://www.google.com")
    
    try:
        session_id = await browser_automation.create_session(url)
        
        session = BrowserSession(
            id=session_id,
            url=url,
            connected=True,
            created_at=datetime.now()
        )
        
        active_sessions[session_id] = session
        
        await websocket_manager.send_message(websocket, {
            "type": "browser-status",
            "connected": True,
            "sessionId": session_id,
            "url": url
        })
        
        logger.info(f"Browser session created: {session_id}")
        
    except Exception as e:
        logger.error(f"Failed to create browser session: {e}")
        await websocket_manager.send_message(websocket, {
            "type": "browser-status",
            "connected": False,
            "error": str(e)
        })

async def handle_disconnect_browser(websocket: WebSocket, message: Dict[str, Any]):
    """Handle browser disconnection request"""
    session_id = message.get("sessionId")
    
    if session_id and session_id in active_sessions:
        try:
            await browser_automation.close_session(session_id)
            del active_sessions[session_id]
            
            await websocket_manager.send_message(websocket, {
                "type": "browser-status",
                "connected": False,
                "sessionId": None
            })
            
            logger.info(f"Browser session closed: {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to close browser session: {e}")

async def handle_execute_command(websocket: WebSocket, message: Dict[str, Any]):
    """Handle command execution request"""
    session_id = message.get("sessionId")
    command = message.get("command")
    
    if not session_id or session_id not in active_sessions:
        await websocket_manager.send_message(websocket, {
            "type": "command-result",
            "success": False,
            "error": "No active browser session"
        })
        return
    
    try:
        result = await browser_automation.execute_command(session_id, command)
        
        await websocket_manager.send_message(websocket, {
            "type": "command-result",
            "success": True,
            "command": command.get("command"),
            "result": result
        })
        
        logger.info(f"Command executed successfully: {command.get('command')}")
        
    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        await websocket_manager.send_message(websocket, {
            "type": "command-result",
            "success": False,
            "command": command.get("command"),
            "error": str(e)
        })

async def handle_take_screenshot(websocket: WebSocket, message: Dict[str, Any]):
    """Handle screenshot request"""
    session_id = message.get("sessionId")
    
    if not session_id or session_id not in active_sessions:
        await websocket_manager.send_message(websocket, {
            "type": "screenshot-result",
            "success": False,
            "error": "No active browser session"
        })
        return
    
    try:
        screenshot_data = await browser_automation.take_screenshot(session_id)
        
        await websocket_manager.send_message(websocket, {
            "type": "screenshot-result",
            "success": True,
            "screenshot": screenshot_data,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(f"Screenshot captured for session: {session_id}")
        
    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        await websocket_manager.send_message(websocket, {
            "type": "screenshot-result",
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
