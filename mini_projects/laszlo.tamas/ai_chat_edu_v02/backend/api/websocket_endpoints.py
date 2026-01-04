"""
WebSocket endpoints for real-time workflow state streaming.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/workflow/{session_id}")
async def websocket_workflow_state(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming workflow state updates.
    
    Client connects with session_id and receives real-time state updates
    as the workflow progresses through nodes.
    
    Args:
        websocket: WebSocket connection
        session_id: Chat session identifier
    """
    await websocket_manager.connect(session_id, websocket)
    
    try:
        # Keep connection alive and wait for disconnect
        while True:
            # Receive ping/pong messages to keep connection alive
            data = await websocket.receive_text()
            
            if data == "ping":
                await websocket.send_text("pong")
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket disconnected for session {session_id}")
    
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}", exc_info=True)
        websocket_manager.disconnect(session_id, websocket)
