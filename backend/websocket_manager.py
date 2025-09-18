import asyncio
import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_data: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_data[websocket] = {
            "connected_at": asyncio.get_event_loop().time(),
            "session_id": None
        }
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_data:
            del self.connection_data[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            self.disconnect(websocket)

    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSockets"""
        if not self.active_connections:
            return
        
        disconnected = []
        for websocket in self.active_connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(websocket)
        
        # Remove disconnected WebSockets
        for websocket in disconnected:
            self.disconnect(websocket)


    async def disconnect_all(self):
        """Disconnect all WebSocket connections"""
        for websocket in self.active_connections.copy():
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")
        
        self.active_connections.clear()
        self.connection_data.clear()
        logger.info("All WebSocket connections closed")

    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
