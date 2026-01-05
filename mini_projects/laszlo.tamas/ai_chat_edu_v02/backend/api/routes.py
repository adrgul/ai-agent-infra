import logging
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from api.schemas import (
    ChatRequest, ChatResponse, RAGChatRequest, RAGChatResponse,
    MessageResponse, ErrorResponse, UserUpdateRequest, TenantUpdateRequest
)
from services.unified_chat_workflow import UnifiedChatWorkflow
from database.models import User
from database.pg_connection import check_db_connection
from database.pg_init import (
    get_active_tenants, get_all_tenants, get_users_by_tenant, 
    get_user_by_id_pg, get_tenant_by_id, create_session_pg, insert_message_pg
)
from config.prompts import build_system_prompt
from config.settings import CONSOLIDATE_AFTER_MESSAGES
from services.cache_service import simple_cache

# Import retrieval router
from api.retrieval import router as retrieval_router
# Import debug router
from api.debug_endpoints import router as debug_router
# Import workflow router
from api.workflow_endpoints import router as workflow_router
# Import admin router (P0.17 - Cache Control)
from api.admin_endpoints import router as admin_router

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize workflows
openai_api_key = os.getenv("OPENAI_API_KEY")
if openai_api_key:
    # Unified workflow (agent-based)
    unified_workflow = UnifiedChatWorkflow(openai_api_key)
    logger.info("✅ UnifiedChatWorkflow initialized")
else:
    unified_workflow = None
    logger.warning("OPENAI_API_KEY not set, workflows disabled")

# Include retrieval router
router.include_router(retrieval_router)
# Include debug router
router.include_router(debug_router)
# Include workflow router
router.include_router(workflow_router)
# Include admin router (P0.17 - Cache Control)
router.include_router(admin_router)


@router.get("/tenants")
async def get_tenants(active_only: bool = True):
    """Get all tenants or only active ones."""
    try:
        # Try cache first
        cache_key = f"tenants:active={active_only}"
        cached_tenants = simple_cache.get(cache_key)
        
        if cached_tenants is not None:
            logger.info(f"🟢 Cache HIT: {cache_key}")
            return cached_tenants
        
        # Cache MISS - fetch from DB
        logger.info(f"🔴 Cache MISS: {cache_key}")
        if active_only:
            tenants = get_active_tenants()
        else:
            tenants = get_all_tenants()
        
        # Store in cache (5 min TTL)
        simple_cache.set(cache_key, tenants, ttl_seconds=300)
        return tenants
    except Exception as e:
        logger.error(f"Error fetching tenants: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tenants"
        )


@router.get("/users")
async def get_users(tenant_id: int | None = None):
    """Get all users for the dropdown, optionally filtered by tenant."""
    try:
        # Try cache first
        cache_key = f"users:tenant={tenant_id}"
        cached_users = simple_cache.get(cache_key)
        
        if cached_users is not None:
            logger.info(f"🟢 Cache HIT: {cache_key}")
            return cached_users
        
        # Cache MISS - fetch from DB
        logger.info(f"🔴 Cache MISS: {cache_key}")
        if tenant_id:
            # Get users from PostgreSQL filtered by tenant
            users = get_users_by_tenant(tenant_id)
        else:
            # Get all users from PostgreSQL (no tenant filter)
            from database.pg_init import get_all_users_pg
            users = get_all_users_pg()
        
        # Store in cache (5 min TTL)
        simple_cache.set(cache_key, users, ttl_seconds=300)
        return users
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch users"
        )


@router.get("/db-check")
async def check_database_connection():
    """Check PostgreSQL database connection health."""
    try:
        success, message = check_db_connection()
        if success:
            return {"status": "success", "message": message}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=message
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking database connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adatbázis kapcsolódás sikertelen! Hiba: {str(e)}"
        )


@router.get("/chat/{session_id}/messages", response_model=list[MessageResponse])
async def get_session_messages(session_id: str):
    """Get all messages for a chat session."""
    try:
        from database.pg_init import get_session_messages_pg
        messages = get_session_messages_pg(session_id, limit=100)  # Get more messages
        return messages
    except Exception as e:
        logger.error(f"Error fetching session messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch session messages"
        )


# Removed deprecated /chat/basic endpoint - use /chat (unified workflow) instead


@router.get("/debug/{user_id}")
async def get_debug_info(user_id: int):
    """
    Get debug information for a user:
    - User data from database
    - Last 10 message exchanges
    """
    try:
        # Get user data from PostgreSQL
        from database.pg_init import get_user_by_id_pg, get_last_messages_for_user_pg
        
        user = get_user_by_id_pg(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Get last messages from PostgreSQL (limit to last 20 for performance)
        messages = get_last_messages_for_user_pg(user_id, limit=20)
        
        # Format messages into exchanges (pairs of user + assistant)
        exchanges = []
        temp_exchange = {}
        for msg in messages:
            if msg["role"] == "user":
                temp_exchange = {
                    "timestamp": str(msg["created_at"]),  # Convert datetime to string
                    "user_message": msg["content"],
                    "assistant_message": None
                }
            elif msg["role"] == "assistant" and temp_exchange:
                temp_exchange["assistant_message"] = msg["content"]
                exchanges.append(temp_exchange)
                temp_exchange = {}
        
        # Keep only last 10 exchanges
        exchanges = exchanges[-10:]
        # Get documents accessible to the user
        from database.pg_init import get_documents_for_user
        documents = get_documents_for_user(user_id=user_id, tenant_id=user['tenant_id'])
        
        # Build LangGraph state representation (like it would be in workflow)
        from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
        
        # Get tenant for hierarchical prompt
        tenant = get_tenant_by_id(user['tenant_id'])
        
        # Build hierarchical system prompt
        system_content = build_system_prompt(
            user_context=user,
            tenant_prompt=tenant.get('system_prompt') if tenant else None,
            user_prompt=user.get('system_prompt')
        )
        
        system_msg = {
            "type": "system",
            "content": system_content
        }
        
        # Convert messages to LangGraph state format
        langgraph_messages = [system_msg]
        for msg in messages:
            langgraph_messages.append({
                "type": "human" if msg["role"] == "user" else "ai",
                "content": msg["content"],
                "timestamp": msg["created_at"]
            })
        
        # Build all workflow states
        chat_state = {
            "messages": langgraph_messages,
            "user_context": {
                "user_id": user["user_id"],
                "tenant_id": user["tenant_id"],
                "nickname": user["nickname"],
                "firstname": user["firstname"],
                "lastname": user["lastname"],
                "role": user["role"],
                "default_lang": user["default_lang"]
            },
            "total_messages": len(langgraph_messages)
        }
        
        # RAG Workflow State (example/template)
        rag_state = {
            "query": None,
            "user_context": {
                "tenant_id": user["tenant_id"],
                "user_id": user["user_id"],
                "tenant_prompt": tenant.get('system_prompt') if tenant else None,
                "user_prompt": user.get('system_prompt'),
                "user_language": user.get("default_lang", "hu")
            },
            "system_prompt": None,
            "combined_prompt": None,
            "needs_rag": False,
            "retrieved_chunks": [],
            "has_relevant_context": False,
            "final_answer": None,
            "sources": [],
            "error": None
        }
        
        # Document Processing Workflow State (example/template)
        document_processing_state = {
            "filename": None,
            "file_type": None,
            "tenant_id": user["tenant_id"],
            "user_id": user["user_id"],
            "visibility": None,
            "extracted_text": None,
            "document_id": None,
            "chunk_ids": [],
            "embedding_count": 0,
            "qdrant_point_ids": [],
            "status": "idle",
            "error": None,
            "processing_summary": {}
        }
        
        # Session Memory Workflow State (example/template)
        session_memory_state = {
            "session_id": None,
            "tenant_id": user["tenant_id"],
            "user_id": user["user_id"],
            "session_data": None,
            "interactions": [],
            "interaction_count": 0,
            "needs_summary": False,
            "summary_text": None,
            "embedding_vector": None,
            "qdrant_point_id": None,
            "ltm_id": None,
            "status": "idle",
            "error": None,
            "processing_summary": {}
        }
        
        return {
            "user_data": user,
            "last_exchanges": exchanges,
            "accessible_documents": documents,
            "workflow_states": {
                "chat": chat_state,
                "rag": rag_state,
                "document_processing": document_processing_state,
                "session_memory": session_memory_state
            }
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
        # Verify user exists in PostgreSQL
        from database.pg_init import get_user_by_id_pg, delete_user_conversation_history_pg
        
        user = get_user_by_id_pg(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        
        # Delete all conversation history from PostgreSQL
        delete_user_conversation_history_pg(user_id)
        
        return {"message": f"All conversation history deleted for user {user['firstname']} {user['lastname']}"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation history: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation history: {str(e)}"
        )


@router.get("/howto/files")
async def get_howto_files():
    """
    Get list of all HOW_TO_*.md files from the docs directory (mounted in Docker).
    Returns: List of filenames without path.
    """
    try:
        # In Docker, docs directory is mounted at /docs
        docs_dir = Path("/docs")
        
        # Find all HOW_TO_*.md files
        howto_files = []
        for file_path in docs_dir.glob("HOW_TO*.md"):
            if file_path.is_file():
                howto_files.append(file_path.name)
        
        # Sort files alphabetically
        howto_files.sort()
        
        logger.info(f"Found {len(howto_files)} HOW_TO files: {howto_files}")
        
        return {"files": howto_files}
    
    except Exception as e:
        logger.error(f"Error fetching HOW_TO files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch HOW_TO files: {str(e)}"
        )


@router.get("/howto/{filename}", response_class=PlainTextResponse)
async def get_howto_content(filename: str):
    """
    Get the content of a specific HOW_TO file.
    Filename must match pattern HOW_TO*.md for security.
    """
    try:
        # Security check: only allow HOW_TO*.md or HOW_TO.md files
        if not (filename == "HOW_TO.md" or (filename.startswith("HOW_TO") and filename.endswith(".md"))):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename. Only HOW_TO*.md files are allowed."
            )
        
        # In Docker, docs directory is mounted at /docs
        file_path = Path("/docs") / filename
        
        # Check if file exists
        if not file_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File {filename} not found"
            )
        
        # Read and return file content
        content = file_path.read_text(encoding="utf-8")
        logger.info(f"Successfully read {filename} ({len(content)} bytes)")
        return content
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading HOW_TO file {filename}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )


@router.post("/chat/rag", response_model=RAGChatResponse, responses={
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse}
})
@router.post("/chat", response_model=RAGChatResponse, responses={
    400: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
    503: {"model": ErrorResponse}
})
async def chat_rag(request: RAGChatRequest):
    """
    Unified chat endpoint with agent-based routing (LangGraph workflow).
    
    Pipeline:
    1. Session management (create/validate session)
    2. Persist user message
    3. Execute UnifiedChatWorkflow (agent decides: CHAT | RAG | LIST)
    4. Persist assistant message
    5. Return response with session context
    
    Agent routes:
    - CHAT: Personal conversation with user context + chat history
    - RAG: Document search (embedding -> Qdrant -> PostgreSQL -> LLM)
    - LIST: Document listing (metadata + titles)
    
    Returns:
        RAGChatResponse with answer, source document IDs, session_id, and error (if any)
    
    Raises:
        400: Invalid input
        503: Workflow not available (OPENAI_API_KEY missing)
        500: Workflow execution error
    """
    if not unified_workflow:
        logger.error("Unified workflow not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workflow not available. Check OPENAI_API_KEY configuration."
        )
    
    # Step 1: Session management
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        create_session_pg(session_id, request.tenant_id, request.user_id)
        logger.info(f"Session {session_id} ready for user {request.user_id}")
    except Exception as e:
        # Session might already exist, which is fine
        logger.debug(f"Session creation note: {e}")
    
    logger.info(
        f"Chat request: user_id={request.user_id}, tenant_id={request.tenant_id}, "
        f"session_id={session_id}, query='{request.query[:50]}...'"
    )
    
    # Step 2: Persist user message
    try:
        insert_message_pg(session_id, request.tenant_id, request.user_id, "user", request.query)
        logger.info(f"User message saved to session {session_id}")
    except Exception as e:
        logger.error(f"Failed to save user message: {e}")
        # Continue anyway - message persistence should not block chat
    
    # Step 3: Execute UnifiedChatWorkflow (agent-based routing)
    try:
        # Enable WebSocket broadcast for real-time debug panel updates
        unified_workflow.enable_websocket_broadcast(session_id, True)
        
        result = unified_workflow.execute(
            query=request.query,
            session_id=session_id,
            user_context={
                "tenant_id": request.tenant_id,
                "user_id": request.user_id
            }
        )
        
        logger.info(
            f"Unified workflow complete: answer_len={len(result['final_answer'])}, "
            f"sources={result['sources']}, actions={result.get('actions_taken', [])}"
        )
        
        assistant_answer = result["final_answer"]
        prompt_details = result.get("prompt_details")
        
        logger.info(f"Prompt details available: {prompt_details is not None}")
        if prompt_details:
            logger.info(f"Prompt details keys: {list(prompt_details.keys())}")
        
        # Step 4: Persist assistant message with metadata
        try:
            insert_message_pg(
                session_id=session_id,
                tenant_id=request.tenant_id,
                user_id=request.user_id,
                role="assistant",
                content=assistant_answer,
                metadata={
                    "sources": result.get("sources", []),
                    "rag_params": result.get("rag_params"),
                    "actions_taken": result.get("actions_taken"),
                    "workflow_path": result.get("workflow_path", "UNKNOWN")
                }
            )
            logger.info(f"Assistant message saved to session {session_id}")
        except Exception as e:
            logger.error(f"Failed to save assistant message: {e}")
        
        return RAGChatResponse(
            answer=assistant_answer,
            sources=result["sources"],
            error=result.get("error"),
            session_id=session_id,
            prompt_details=prompt_details,
            rag_params=result.get("rag_params")
        )
    
    except Exception as e:
        logger.error(f"Unified workflow error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow error: {str(e)}"
        )


@router.get("/users/{user_id}")
async def get_user(user_id: int):
    """Get single user by ID."""
    try:
        # Try cache first
        cache_key = f"user:{user_id}"
        cached_user = simple_cache.get(cache_key)
        
        if cached_user is not None:
            logger.info(f"🟢 Cache HIT: {cache_key}")
            return cached_user
        
        # Cache MISS - fetch from DB
        logger.info(f"🔴 Cache MISS: {cache_key}")
        user = get_user_by_id_pg(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        user_dict = {
            "user_id": user["user_id"],
            "tenant_id": user["tenant_id"],
            "firstname": user["firstname"],
            "lastname": user["lastname"],
            "nickname": user["nickname"],
            "email": user["email"],
            "role": user["role"],
            "default_lang": user["default_lang"],
            "system_prompt": user["system_prompt"],
            "is_active": user["is_active"],
            "created_at": str(user["created_at"]),
            # "updated_at": str(user["updated_at"]) if "updated_at" in user else None
        }
        # Store in cache (5 min TTL)
        simple_cache.set(cache_key, user_dict, ttl_seconds=300)
        return user_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user"
        )


@router.patch("/users/{user_id}")
async def update_user(user_id: int, updates: UserUpdateRequest):
    """Update user data. Returns updated user."""
    try:
        from database.pg_connection import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Build UPDATE query dynamically
            update_fields = []
            values = []
            if updates.firstname is not None:
                update_fields.append("firstname = %s")
                values.append(updates.firstname)
            if updates.lastname is not None:
                update_fields.append("lastname = %s")
                values.append(updates.lastname)
            if updates.nickname is not None:
                update_fields.append("nickname = %s")
                values.append(updates.nickname)
            if updates.email is not None:
                update_fields.append("email = %s")
                values.append(updates.email)
            if updates.role is not None:
                update_fields.append("role = %s")
                values.append(updates.role)
            if updates.default_lang is not None:
                update_fields.append("default_lang = %s")
                values.append(updates.default_lang)
            if updates.system_prompt is not None:
                update_fields.append("system_prompt = %s")
                values.append(updates.system_prompt)
            if updates.is_active is not None:
                update_fields.append("is_active = %s")
                values.append(updates.is_active)
            if not update_fields:
                raise HTTPException(status_code=400, detail="No fields to update")
            # Add updated_at timestamp
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s RETURNING *"
            cursor.execute(query, values)
            updated_user = cursor.fetchone()
            if not updated_user:
                raise HTTPException(status_code=404, detail="User not found")
            # Clear cache
            simple_cache.delete(f"user:{user_id}")
            simple_cache.clear_pattern("users:tenant=")
            logger.info(f"✅ User {user_id} updated successfully")
            return {
                "success": True,
                "user": {
                    "user_id": updated_user[0],
                    "tenant_id": updated_user[1],
                    "firstname": updated_user[2],
                    "lastname": updated_user[3],
                "nickname": updated_user[4],
                "email": updated_user[5],
                "role": updated_user[6],
                "default_lang": updated_user[7],
                "system_prompt": updated_user[8],
                "is_active": updated_user[9],
                "created_at": str(updated_user[10]),
                "updated_at": str(updated_user[11])
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.get("/tenants/{tenant_id}")
async def get_tenant(tenant_id: int):
    """Get single tenant by ID."""
    try:
        # Try cache first
        cache_key = f"tenant:{tenant_id}"
        cached_tenant = simple_cache.get(cache_key)
        
        if cached_tenant is not None:
            logger.info(f"🟢 Cache HIT: {cache_key}")
            return cached_tenant
        
        # Cache MISS - fetch from DB
        logger.info(f"🔴 Cache MISS: {cache_key}")
        tenant = get_tenant_by_id(tenant_id)
        
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        import json
        tenant_dict = {
            "id": tenant[0],  # tenant_id
            "name": tenant[1],
            "description": tenant[2],
            "system_prompt": tenant[3],
            "is_active": tenant[4],
            "settings": json.loads(tenant[5]) if tenant[5] else None,
            "created_at": str(tenant[6]),
            "updated_at": str(tenant[7])
        }
        
        # Store in cache (5 min TTL)
        simple_cache.set(cache_key, tenant_dict, ttl_seconds=300)
        return tenant_dict
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching tenant {tenant_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch tenant"
        )


@router.patch("/tenants/{tenant_id}")
async def update_tenant(tenant_id: int, updates: TenantUpdateRequest):
    """Update tenant data. Returns updated tenant. Admin only."""
    try:
        from database.pg_connection import get_db_connection
        import json
        with get_db_connection() as conn:
            cursor = conn.cursor()
        
        # Build UPDATE query dynamically
        update_fields = []
        values = []
        
        if updates.name is not None:
            update_fields.append("name = %s")
            values.append(updates.name)
        if updates.description is not None:
            update_fields.append("description = %s")
            values.append(updates.description)
        if updates.system_prompt is not None:
            update_fields.append("system_prompt = %s")
            values.append(updates.system_prompt)
        if updates.is_active is not None:
            update_fields.append("is_active = %s")
            values.append(updates.is_active)
        if updates.settings is not None:
            update_fields.append("settings = %s")
            values.append(json.dumps(updates.settings))
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Add updated_at timestamp
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        
        values.append(tenant_id)
        query = f"UPDATE tenants SET {', '.join(update_fields)} WHERE tenant_id = %s RETURNING *"
        
        cursor.execute(query, values)
        updated_tenant = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()
        
        if not updated_tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        
        # Clear cache
        simple_cache.clear_pattern("tenants:active=")
        
        logger.info(f"✅ Tenant {tenant_id} updated successfully")
        
        return {
            "success": True,
            "tenant": {
                "tenant_id": updated_tenant[0],
                "name": updated_tenant[1],
                "description": updated_tenant[2],
                "system_prompt": updated_tenant[3],
                "is_active": updated_tenant[4],
                "settings": json.loads(updated_tenant[5]) if updated_tenant[5] else None,
                "created_at": str(updated_tenant[6]),
                "updated_at": str(updated_tenant[7])
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating tenant {tenant_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )
