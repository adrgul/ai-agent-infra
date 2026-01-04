import logging
from fastapi import APIRouter, HTTPException, status
from api.schemas import ChatRequest, ChatResponse, MessageResponse, ErrorResponse
from services.chat_service import ChatService
from database.db import get_all_users, get_user_by_id, get_last_messages_for_user
from database.models import User

logger = logging.getLogger(__name__)

router = APIRouter()
chat_service = ChatService()


@router.get("/users", response_model=list[User])
async def get_users():
    """Get all users for the dropdown."""
    try:
        users = get_all_users()
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.get("/chat/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(session_id: str):
    """Get all messages for a chat session."""
    try:
        from database.db import get_session_messages
        messages = get_session_messages(session_id, limit=100)  # Get more messages
        return messages
    except Exception as e:
        logger.error(f"Error fetching session messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session messages"
        )


@router.post("/chat", response_model=ChatResponse, responses={
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse}
})
async def chat(request: ChatRequest):
    """
    Process a chat message.
    
    Steps:
    1. Validate user exists and is active
    2. Load user record from SQLite
    3. Load last N messages for the session
    4. Build LLM context with user identity
    5. Call OpenAI Chat Completion API
    6. Persist both user and assistant messages
    7. Return assistant response
    """
    try:
        logger.info(f"Chat request: user_id={request.user_id}, session_id={request.session_id}")
        
        assistant_reply = chat_service.process_chat_message(
            user_id=request.user_id,
            session_id=request.session_id,
            message=request.message
        )
        
        return ChatResponse(answer=assistant_reply)
    
    except ValueError as e:
        # User validation errors
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except RuntimeError as e:
        # OpenAI API errors (already logged in service)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    
    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again."
        )


@router.get("/debug/{user_id}")
async def get_debug_info(user_id: int):
    """
    Get debug information for a user:
    - User data from database
    - AI-generated summary of what we know about the user
    - Last 10 message exchanges
    """
    try:
        # Get user data
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Get last messages
        messages = get_last_messages_for_user(user_id, limit=10)
        
        # Generate AI summary
        user_summary = chat_service.generate_user_summary(user_id, messages)
        
        # Format messages into exchanges (pairs of user + assistant)
        exchanges = []
        temp_exchange = {}
        for msg in messages[-20:]:  # Look at last 20 to get 10 exchanges
            if msg["role"] == "user":
                temp_exchange = {
                    "timestamp": msg["created_at"],
                    "user_message": msg["content"],
                    "assistant_message": None
                }
            elif msg["role"] == "assistant" and temp_exchange:
                temp_exchange["assistant_message"] = msg["content"]
                exchanges.append(temp_exchange)
                temp_exchange = {}
        
        # Keep only last 10 exchanges
        exchanges = exchanges[-10:]
        
        return {
            "user_data": user,
            "ai_summary": user_summary,
            "last_exchanges": exchanges
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching debug info: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch debug information: {str(e)}"
        )


@router.delete("/debug/{user_id}/conversations")
async def delete_user_conversations(user_id: int):
    """
    Delete all conversation history for a specific user.
    This includes all messages and sessions.
    """
    try:
        # Verify user exists
        user = get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Delete all conversation history
        from database.db import delete_user_conversation_history
        delete_user_conversation_history(user_id)
        
        return {"message": f"All conversation history deleted for user {user['firstname']} {user['lastname']}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation history: {str(e)}"
        )
