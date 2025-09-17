"""
Voice-Enabled Browser Agent Backend
Main FastAPI application with STT, intent parsing, and planning capabilities
"""

import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, List, Optional, Any
import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from services.stt_service import STTService
from services.intent_parser import IntentParser
from services.planner import Planner
from services.archive_service import ArchiveService
from services.monitoring import MonitoringService
from models.schemas import (
    AudioChunk, TranscriptResponse, IntentResponse, 
    ExecutionRequest, ExecutionResponse, SessionData
)

# Load environment variables
load_dotenv()

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Global services
stt_service: Optional[STTService] = None
intent_parser: Optional[IntentParser] = None
planner: Optional[Planner] = None
archive_service: Optional[ArchiveService] = None
monitoring_service: Optional[MonitoringService] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    global stt_service, intent_parser, planner, archive_service, monitoring_service
    
    logger.info("Initializing Voice Agent services...")
    
    try:
        # Initialize monitoring first
        monitoring_service = MonitoringService()
        await monitoring_service.initialize()
        
        # Initialize STT service
        stt_service = STTService(monitoring_service)
        await stt_service.initialize()
        
        # Initialize intent parser
        intent_parser = IntentParser(monitoring_service)
        await intent_parser.initialize()
        
        # Initialize planner
        planner = Planner(monitoring_service)
        await planner.initialize()
        
        # Initialize archive service
        archive_service = ArchiveService(monitoring_service)
        await archive_service.initialize()
        
        logger.info("All services initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize services", error=str(e))
        raise
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down services...")
    if monitoring_service:
        await monitoring_service.shutdown()

# Create FastAPI app
app = FastAPI(
    title="Voice-Enabled Browser Agent",
    description="AI-powered browser automation with voice control",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_data: Dict[str, SessionData] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.session_data[session_id] = SessionData(session_id=session_id)
        logger.info("WebSocket connected", session_id=session_id)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if session_id in self.session_data:
            del self.session_data[session_id]
        logger.info("WebSocket disconnected", session_id=session_id)

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error("Failed to send WebSocket message", error=str(e))

manager = ConnectionManager()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Voice-Enabled Browser Agent API", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "stt": stt_service.is_healthy() if stt_service else False,
            "intent_parser": intent_parser.is_healthy() if intent_parser else False,
            "planner": planner.is_healthy() if planner else False,
            "archive": archive_service.is_healthy() if archive_service else False,
            "monitoring": monitoring_service.is_healthy() if monitoring_service else False,
        }
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Main WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive audio chunk or other messages
            data = await websocket.receive_bytes()
            
            # Process audio chunk
            audio_chunk = AudioChunk(
                session_id=session_id,
                audio_data=data,
                timestamp=asyncio.get_event_loop().time()
            )
            
            # Process through pipeline
            await process_audio_pipeline(audio_chunk, websocket, session_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
    except Exception as e:
        logger.error("WebSocket error", error=str(e), session_id=session_id)
        manager.disconnect(websocket, session_id)

async def process_audio_pipeline(audio_chunk: AudioChunk, websocket: WebSocket, session_id: str):
    """Process audio through the complete pipeline"""
    try:
        # Step 1: Speech-to-Text
        transcript_response = await stt_service.process_audio(audio_chunk)
        
        if transcript_response.transcript:
            await manager.send_personal_message({
                "type": "transcript",
                "data": transcript_response.dict()
            }, websocket)
            
            # Step 2: Intent Parsing
            intent_response = await intent_parser.parse_intent(
                transcript_response.transcript, 
                session_id
            )
            
            await manager.send_personal_message({
                "type": "intent",
                "data": intent_response.dict()
            }, websocket)
            
            # Step 3: Planning
            if intent_response.confidence > 0.7:  # Only proceed with high confidence
                execution_request = await planner.create_execution_plan(
                    intent_response, 
                    session_id
                )
                
                await manager.send_personal_message({
                    "type": "execution_plan",
                    "data": execution_request.dict()
                }, websocket)
                
                # Step 4: Execute browser actions (via executor service)
                execution_response = await execute_browser_actions(execution_request)
                
                await manager.send_personal_message({
                    "type": "execution_result",
                    "data": execution_response.dict()
                }, websocket)
                
                # Step 5: Archive results
                await archive_service.archive_session_data(
                    session_id,
                    transcript_response,
                    intent_response,
                    execution_response
                )
        
    except Exception as e:
        logger.error("Pipeline processing error", error=str(e), session_id=session_id)
        await manager.send_personal_message({
            "type": "error",
            "data": {"error": str(e)}
        }, websocket)

async def execute_browser_actions(execution_request: ExecutionRequest) -> ExecutionResponse:
    """Execute browser actions via the executor service"""
    import httpx
    
    try:
        # Send execution request to the Node.js executor service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3001/api/execute",
                json={
                    "sessionId": execution_request.session_id,
                    "actions": [action.dict() for action in execution_request.actions],
                    "context": execution_request.context
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                return ExecutionResponse(
                    session_id=execution_request.session_id,
                    success=result["success"],
                    actions_executed=execution_request.actions,
                    screenshots=result.get("result", {}).get("screenshots", []),
                    final_url=result.get("result", {}).get("final_url"),
                    execution_time=result.get("result", {}).get("execution_time", 0),
                    error_message=result.get("error")
                )
            else:
                return ExecutionResponse(
                    session_id=execution_request.session_id,
                    success=False,
                    actions_executed=[],
                    screenshots=[],
                    execution_time=0,
                    error_message=f"Executor service error: {response.status_code}"
                )
                
    except Exception as e:
        logger.error("Failed to execute browser actions", error=str(e), session_id=execution_request.session_id)
        return ExecutionResponse(
            session_id=execution_request.session_id,
            success=False,
            actions_executed=[],
            screenshots=[],
            execution_time=0,
            error_message=str(e)
        )

@app.post("/api/export/{session_id}")
async def export_session(session_id: str):
    """Export session data"""
    if not archive_service:
        raise HTTPException(status_code=500, detail="Archive service not available")
    
    try:
        export_data = await archive_service.export_session(session_id)
        return JSONResponse(content=export_data)
    except Exception as e:
        logger.error("Export failed", error=str(e), session_id=session_id)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions")
async def list_sessions():
    """List all available sessions"""
    if not archive_service:
        raise HTTPException(status_code=500, detail="Archive service not available")
    
    try:
        sessions = await archive_service.list_sessions()
        return {"sessions": sessions}
    except Exception as e:
        logger.error("Failed to list sessions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/metrics")
async def get_metrics():
    """Get system metrics"""
    if not monitoring_service:
        raise HTTPException(status_code=500, detail="Monitoring service not available")
    
    try:
        metrics = await monitoring_service.get_metrics_summary()
        return metrics
    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our structured logging
    )
