"""
WebSocket Manager for real-time workflow state broadcasting.

Manages WebSocket connections per session_id and broadcasts state updates
to connected clients.
"""

import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Centralized WebSocket connection manager.
    
    Maintains active connections per session_id and provides
    broadcast functionality for workflow state updates.
    """
    
    def __init__(self):
        # session_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        logger.info("WebSocketManager initialized")
    
    async def connect(self, session_id: str, websocket: WebSocket):
        """Add new WebSocket connection for session."""
        await websocket.accept()
        
        if session_id not in self.active_connections:
            self.active_connections[session_id] = set()
        
        self.active_connections[session_id].add(websocket)
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {len(self.active_connections[session_id])}")
    
    def disconnect(self, session_id: str, websocket: WebSocket):
        """Remove WebSocket connection."""
        if session_id in self.active_connections:
            self.active_connections[session_id].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]
            
            logger.info(f"WebSocket disconnected for session {session_id}")
    
    async def broadcast_state(self, session_id: str, node_name: str, state_data: dict):
        """
        Broadcast workflow state update to all connected clients for this session.
        
        Args:
            session_id: Session identifier
            node_name: Current workflow node name
            state_data: Serialized state snapshot
        """
        if session_id not in self.active_connections:
            return
        
        message = {
            "type": "workflow_state_update",
            "node": node_name,
            "state": state_data,
            "timestamp": None  # Will be set by frontend
        }
        
        # Send to all connected clients for this session
        disconnected = []
        for websocket in self.active_connections[session_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            self.disconnect(session_id, ws)
        
        logger.debug(f"Broadcasted state update for session {session_id}, node {node_name}")


# Global singleton instance
websocket_manager = WebSocketManager()
