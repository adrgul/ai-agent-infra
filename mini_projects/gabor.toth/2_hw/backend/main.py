"""FastAPI application for RAG agent."""

import os
import sys
import json
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
import uuid
import asyncio
from datetime import datetime
from collections import deque

# FIRST: Set working directory to project root BEFORE any relative path operations
# This ensures relative paths like "data/uploads" work correctly
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
os.chdir(PROJECT_ROOT)

# Add backend dir to path for relative imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from domain.models import UserProfile, Message, MessageRole
from domain.interfaces import ActivityCallback
from infrastructure.embedding import OpenAIEmbeddingService
from infrastructure.vector_store import ChromaVectorStore
from infrastructure.chunker import TiktokenChunker
from infrastructure.category_router import OpenAICategoryRouter
from infrastructure.rag_answerer import OpenAIRAGAnswerer
from infrastructure.repositories import (
    JSONUserProfileRepository, JSONSessionRepository, FileUploadRepository
)
from services.upload_service import UploadService
from services.rag_agent import create_rag_agent, RAGAgent
from services.chat_service import ChatService


# Activity callback implementation for logging to frontend
class QueuedActivityCallback(ActivityCallback):
    """Activity callback that stores events in a deque for the frontend."""
    
    def __init__(self, max_size: int = 1000):
        self.events: deque = deque(maxlen=max_size)
    
    async def log_activity(self, message: str, activity_type: str = "info", metadata: Optional[dict] = None) -> None:
        """Store activity event in deque."""
        event = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().timestamp() * 1000,  # Convert to milliseconds (JS compatible)
            "message": message,
            "type": activity_type,
            "metadata": metadata or {}
        }
        self.events.append(event)
    
    async def get_activities(self, count: int = 50) -> list:
        """Get recent activities."""
        activities = list(self.events)
        # Return the most recent activities (last 'count' items)
        return activities[-count:] if len(activities) > count else activities


# Global instances
embedding_service: Optional[OpenAIEmbeddingService] = None
vector_store: Optional[ChromaVectorStore] = None
chunker: Optional[TiktokenChunker] = None
category_router: Optional[OpenAICategoryRouter] = None
rag_answerer: Optional[OpenAIRAGAnswerer] = None
profile_repo: Optional[JSONUserProfileRepository] = None
session_repo: Optional[JSONSessionRepository] = None
upload_repo: Optional[FileUploadRepository] = None
upload_service: Optional[UploadService] = None
rag_agent: Optional[RAGAgent] = None
chat_service: Optional[ChatService] = None
activity_callback: Optional[QueuedActivityCallback] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize on startup, cleanup on shutdown."""
    global embedding_service, vector_store, chunker, category_router
    global rag_answerer, profile_repo, session_repo, upload_repo
    global upload_service, rag_agent, chat_service, activity_callback

    # Check required env vars
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY environment variable is required. "
            "Set it before starting the backend."
        )

    # Initialize dependencies
    embedding_service = OpenAIEmbeddingService(openai_api_key)
    vector_store = ChromaVectorStore("data/chroma_db")
    chunker = TiktokenChunker()
    category_router = OpenAICategoryRouter(openai_api_key)
    rag_answerer = OpenAIRAGAnswerer(openai_api_key)
    profile_repo = JSONUserProfileRepository()
    session_repo = JSONSessionRepository()
    upload_repo = FileUploadRepository()
    activity_callback = QueuedActivityCallback()

    # Initialize services
    upload_service = UploadService(
        chunker, embedding_service, vector_store,
        upload_repo, profile_repo, activity_callback
    )

    # Create LangGraph agent
    compiled_graph = create_rag_agent(
        category_router, embedding_service, vector_store, rag_answerer
    )
    rag_agent = RAGAgent(compiled_graph)

    chat_service = ChatService(rag_agent, profile_repo, session_repo, upload_repo, activity_callback)

    print("✓ Backend initialized successfully")
    yield
    print("✓ Backend shutdown")


app = FastAPI(title="RAG Agent API", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Activity logging endpoints
# ============================================================================

@app.get("/api/activities")
async def get_activities(count: int = Query(50, ge=1, le=200)):
    """Get recent activity events."""
    if not activity_callback:
        return {"activities": []}
    activities = await activity_callback.get_activities(count)
    return {"activities": activities}


# ============================================================================
# Description endpoints (simple version)
# ============================================================================

@app.post("/api/desc-save")
async def save_cat_description(
    category: str = Form(...),
    description: str = Form(...),
):
    """Save description. Shared across all users."""
    try:
        if not upload_repo:
            return {"error": "not initialized"}
        await upload_repo.save_description(category, description)
        return {"status": "saved"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/desc-get")
async def get_cat_description(category: str):
    """Get description. Shared across all users."""
    try:
        if not upload_repo:
            return {"description": ""}
        desc = await upload_repo.get_description(category)
        return {"description": desc or ""}
    except Exception as e:
        return {"description": "", "error": str(e)}

@app.post("/api/cat-match")
async def match_cat(
    question: str = Form(...),
):
    """Match category. Returns best matching category for question."""
    try:
        if not upload_repo or not category_router:
            return {"category": None}
        descriptions = await upload_repo.get_all_descriptions()
        if not descriptions:
            return {"category": None}
        
        # Format descriptions for LLM - enhanced with better structure
        desc_lines = []
        for category_slug, desc_text in descriptions.items():
            # Clean up the description text if it contains formatting
            clean_desc = desc_text.strip() if desc_text else ""
            desc_lines.append(f"- **{category_slug.upper()}** (slug: {category_slug}): {clean_desc}")
        
        desc_text = "\n".join(desc_lines)
        print(f"[cat-match] Question: '{question}'")
        print(f"[cat-match] Available descriptions:\n{desc_text}")
        matched = await category_router.route(question, list(descriptions.keys()), desc_text)
        print(f"[cat-match] Matched category: {matched}")
        return {"category": matched, "confidence": 0.8}
    except Exception as e:
        print(f"Error: {e}")
        return {"category": None, "error": str(e)}


# ============================================================================
# Chat endpoints
# ============================================================================

@app.post("/api/chat")
async def chat(
    user_id: str = Form(...),
    session_id: str = Form(...),
    message: str = Form(...),
):
    """Process user message through RAG agent."""
    if not chat_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        # Log to activity feed - chat start
        if activity_callback:
            await activity_callback.log_activity(
                f"💬 Kérdés: {message[:70]}...",
                activity_type="processing"
            )
        
        response = await chat_service.process_message(user_id, session_id, message)
        
        # Log to activity feed - chat complete
        if activity_callback:
            final_answer = response.get("final_answer", "")
            answer_preview = final_answer[:60] if final_answer else "Feldolgozás befejezve"
            await activity_callback.log_activity(
                f"✓ Válasz: {answer_preview}...",
                activity_type="success"
            )
        
        return JSONResponse(response)
    except Exception as e:
        # Log to activity feed - chat error
        if activity_callback:
            await activity_callback.log_activity(
                f"❌ Hiba: {str(e)[:60]}",
                activity_type="error"
            )
        
        return JSONResponse(
            {"error": str(e)},
            status_code=500,
        )


# ============================================================================
# File upload endpoints
# ============================================================================

@app.post("/api/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = Form(...),
    chunk_size_tokens: int = Form(900),
    overlap_tokens: int = Form(150),
    embedding_batch_size: int = Form(100),
):
    """Upload and process document. Uploads are shared across all users."""
    if not upload_service or not category_router or not upload_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        content = await file.read()
        print(f"📤 Upload: category={category}, file={file.filename}, size={len(content)}")
        
        # Log to activity feed
        if activity_callback:
            await activity_callback.log_activity(
                f"📤 Dokumentum feltöltése: {file.filename} ({category} kategória)",
                activity_type="processing"
            )
        
        doc = await upload_service.process_upload(
            file.filename, content, category,
            chunk_size_tokens, overlap_tokens, embedding_batch_size
        )
        
        print(f"✅ Upload success: {doc.upload_id}")
        
        # Log to activity feed - file saved
        if activity_callback:
            await activity_callback.log_activity(
                f"✓ Fájl mentve: {file.filename} ({doc.size:,} bájt)",
                activity_type="success",
                metadata={"upload_id": doc.upload_id, "size": doc.size}
            )
        
        # Generate/enhance category description based on new document
        try:
            # Log category description generation start
            if activity_callback:
                await activity_callback.log_activity(
                    f"🔄 Kategória leírás frissítése: '{category}'",
                    activity_type="processing"
                )
            
            # Get first 500 chars of content for LLM
            text_snippet = content.decode('utf-8', errors='ignore')[:500]
            
            # Get existing description
            existing_desc = await upload_repo.get_description(category)
            
            # Generate new description via LLM
            new_description = await category_router.generate_description(
                category=category,
                new_document_title=file.filename,
                new_document_snippet=text_snippet,
                existing_description=existing_desc
            )
            
            # Update description.json
            category_dir = upload_repo._get_category_dir(category)
            description_file = category_dir / 'description.json'
            
            description_data = {
                "category": category,
                "slug": upload_repo._slugify(category),
                "description": new_description,
                "last_updated": str(Path(description_file).stat().st_mtime if description_file.exists() else 0),
                "keywords": [],
                "topics": []
            }
            
            with open(description_file, 'w', encoding='utf-8') as f:
                json.dump(description_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Description updated for category: {category}")
            
            # Log to activity feed - description updated
            if activity_callback:
                await activity_callback.log_activity(
                    f"✓ Kategória leírás frissítve: '{category}'",
                    activity_type="success",
                    metadata={"category": category}
                )
        except Exception as desc_err:
            print(f"⚠️  Description generation warning (not critical): {desc_err}")
            # Log to activity feed - description generation failed (but not critical)
            if activity_callback:
                await activity_callback.log_activity(
                    f"⚠️ Kategória leírás frissítés sikertelen (nem kritikus): {str(desc_err)[:80]}",
                    activity_type="warning",
                    metadata={"category": category, "error": str(desc_err)[:100]}
                )
            # Don't fail the upload if description generation fails
        
        return JSONResponse({
            "upload_id": doc.upload_id,
            "filename": doc.filename,
            "category": doc.category,
            "size": doc.size,
            "created_at": doc.created_at.isoformat(),
        })
    except Exception as e:
        import traceback
        print(f"❌ Upload error: {e}")
        traceback.print_exc()
        return JSONResponse(
            {"error": str(e), "type": type(e).__name__},
            status_code=400,
        )


@app.delete("/api/files/{upload_id}")
async def delete_file(
    upload_id: str,
    category: str,
    filename: str,
):
    """Delete uploaded document."""
    if not upload_service:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        await upload_service.delete_upload(category, upload_id, filename)
        return JSONResponse({"status": "deleted"})
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


@app.get("/api/files")
async def list_files(user_id: str):
    """List uploaded documents for user."""
    if not upload_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        # Get profile to get categories
        profile = await profile_repo.get_profile(user_id)
        if not profile:
            return JSONResponse([])

        all_uploads = []
        for category in profile.categories:
            uploads = await upload_repo.list_uploads(user_id, category)
            for upload in uploads:
                all_uploads.append({
                    "upload_id": upload.upload_id,
                    "filename": upload.filename,
                    "category": upload.category,
                    "size": upload.size,
                    "created_at": upload.created_at.isoformat(),
                })

        return JSONResponse(all_uploads)
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


# ============================================================================
# Category endpoints
# ============================================================================

@app.get("/api/categories")
async def get_categories():
    """Get all available categories from uploads directory."""
    if not upload_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        categories = []
        base_dir = upload_repo.base_dir
        if base_dir.exists():
            for category_dir in base_dir.iterdir():
                if category_dir.is_dir() and category_dir.name != '.DS_Store':
                    # Check if it has description.json (sign of a valid category)
                    description_file = category_dir / 'description.json'
                    if description_file.exists():
                        categories.append(category_dir.name)
        
        return JSONResponse(sorted(categories))
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


@app.post("/api/categories")
async def create_category(category: str = Form(...)):
    """Create a new empty category directory with description.json."""
    if not upload_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        if not category or not category.strip():
            raise HTTPException(status_code=400, detail="Category name cannot be empty")
        
        category = category.strip()
        category_dir = upload_repo._get_category_dir(category)
        category_dir.mkdir(parents=True, exist_ok=True)
        
        # Create description.json with detailed metadata
        import json
        description_file = category_dir / 'description.json'
        description_data = {
            "category": category,
            "slug": upload_repo._slugify(category),
            "created_at": str(Path(category_dir).stat().st_ctime),
            "description": f"Dokumentumok a '{category}' kategóriához",
            # Add keywords for better LLM routing
            "keywords": [],
            "topics": []
        }
        with open(description_file, 'w', encoding='utf-8') as f:
            json.dump(description_data, f, ensure_ascii=False, indent=2)
        
        return JSONResponse({
            "success": True,
            "category": category,
            "message": f"Category '{category}' created successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


@app.delete("/api/categories")
async def delete_category(category: str = Query(...)):
    """Delete category with all uploads and vector embeddings.
    Tolerant: deletes even if directory doesn't exist anymore."""
    if not upload_repo or not vector_store:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        if not category or not category.strip():
            raise HTTPException(status_code=400, detail="Category name cannot be empty")
        
        category = category.strip()
        category_slug = upload_repo._slugify(category)
        
        # Try to delete from filesystem (won't error if already deleted)
        try:
            await upload_repo.delete_category(category)
            print(f"✓ Deleted filesystem data for: {category}")
        except Exception as e:
            print(f"⚠ Filesystem delete warning: {e}")
        
        # Try to delete from vector store (won't error if collection doesn't exist)
        try:
            collection_name = f"cat_{category_slug}"
            await vector_store.delete_collection(collection_name)
            print(f"✓ Deleted vector store data for: {category}")
        except Exception as e:
            print(f"⚠ Vector store delete warning: {e}")
        
        return JSONResponse({
            "success": True,
            "category": category,
            "message": f"Category '{category}' deleted successfully"
        })
    except Exception as e:
        print(f"Error deleting category: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


@app.get("/api/documents")
async def get_documents(category: str):
    """Get uploaded documents for a category. Shared across all users."""
    if not upload_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        uploads = await upload_repo.list_uploads(category)
        return JSONResponse([
            {
                "upload_id": u.upload_id,
                "filename": u.filename,
                "category": u.category,
                "size": u.size,
                "created_at": u.created_at.isoformat(),
            }
            for u in uploads
        ])
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


# ============================================================================
# Session / History endpoints
# ============================================================================

@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    """Get session messages."""
    if not session_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        messages = await session_repo.get_messages(session_id)
        return JSONResponse([m.to_dict() for m in messages])
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


# ============================================================================
# Profile endpoints
# ============================================================================

@app.get("/api/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile."""
    if not profile_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        profile = await profile_repo.get_profile(user_id)
        if not profile:
            # Return default profile (don't create)
            return JSONResponse({
                "user_id": user_id,
                "language": "hu",
                "categories": [],
                "preferences": {},
            })

        return JSONResponse(profile.to_dict())
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


@app.put("/api/profile/{user_id}")
async def update_profile(user_id: str, profile_data: dict):
    """Update user profile (never delete)."""
    if not profile_repo:
        raise HTTPException(status_code=500, detail="Service not initialized")

    try:
        profile = await profile_repo.get_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)

        # Only allow certain fields
        if "language" in profile_data:
            profile.language = profile_data["language"]
        if "preferences" in profile_data:
            profile.preferences = profile_data["preferences"]

        await profile_repo.save_profile(profile)
        return JSONResponse(profile.to_dict())
    except Exception as e:
        return JSONResponse(
            {"error": str(e)},
            status_code=400,
        )


# ============================================================================
# Health check & Shutdown
# ============================================================================

@app.get("/api/system-info")
async def system_info():
    """Get system information (username, OS)."""
    import getpass
    import platform
    
    username = getpass.getuser()
    system = platform.system()
    
    return {
        "username": username,
        "system": system,
        "display_name": f"{username} ({system})"
    }


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return JSONResponse({"status": "ok"})


@app.post("/api/shutdown")
async def shutdown():
    """Gracefully shutdown the application."""
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🛑 SHUTDOWN KÉRÉS ÉRKEZETT AZ API-TÓL")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("✓ Backend graceful shutdown elindítva...")
    print("")
    
    # Azonnal válaszolunk az ügyfélnek
    response = JSONResponse(
        {"status": "shutting_down", "message": "Server shutting down..."},
        status_code=200
    )
    
    # Leállítás az event loop-ből (2 másodperc múlva)
    def stop_server():
        print("  📍 Backend leállítása szignálküldéssel...")
        import signal
        os.kill(os.getpid(), signal.SIGTERM)
    
    loop = asyncio.get_event_loop()
    loop.call_later(2, stop_server)
    
    return response


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

