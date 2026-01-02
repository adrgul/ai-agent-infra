"""
Session Management API Endpoints (ChatGPT-style)

Handles:
- GET /api/sessions?user_id={id} - List user sessions
- PATCH /api/sessions/{session_id}/title - Update session title
- DELETE /api/sessions/{session_id} - Soft delete session
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from database.pg_init import (
    get_user_sessions,
    update_session_title,
    soft_delete_session
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class UpdateTitleRequest(BaseModel):
    title: str


@router.get("")
async def list_user_sessions(user_id: int = Query(..., description="User ID")):
    """
    Get all sessions for a user, ordered by most recent activity.
    
    Returns sessions with:
    - id, title, created_at, last_message_at
    - message_count, is_deleted, processed_for_ltm
    """
    try:
        sessions = get_user_sessions(user_id, include_deleted=False)
        
        # Format response: title fallback to "Új beszélgetés"
        for session in sessions:
            if not session.get('title'):
                session['title'] = "Új beszélgetés"
        
        logger.info(f"Listed {len(sessions)} sessions for user_id={user_id}")
        return {"sessions": sessions, "count": len(sessions)}
    
    except Exception as e:
        logger.error(f"Error listing sessions for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{session_id}/title")
async def update_title(session_id: str, request: UpdateTitleRequest):
    """
    Update session title (user editing).
    
    Max length: 100 characters
    """
    try:
        if not request.title or len(request.title.strip()) == 0:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
        
        success = update_session_title(session_id, request.title.strip())
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"Updated title for session {session_id}: {request.title[:50]}")
        return {"success": True, "title": request.title.strip()}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating title for session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Soft delete a session (sets is_deleted = TRUE).
    
    Session will no longer appear in session list but data is preserved.
    """
    try:
        success = soft_delete_session(session_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        logger.info(f"Soft deleted session: {session_id}")
        return {"success": True, "session_id": session_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
