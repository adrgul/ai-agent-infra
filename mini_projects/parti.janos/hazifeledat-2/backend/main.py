import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Import domain models
from domain.models import ChatRequest, ChatResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - initialize services on startup."""
    logger.info("Initializing KnowledgeRouter backend...")
    
    # Placeholder for future initializations (DB, Pinecone, LLM)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        logger.info("OPENAI_API_KEY found.")
    else:
        logger.warning("OPENAI_API_KEY not set.")

    yield
    
    logger.info("KnowledgeRouter backend shutting down...")

app = FastAPI(
    title="KnowledgeRouter API",
    description="Backend for AI Knowledge Router & Workflow Automation",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "KnowledgeRouter"}

# Import graph
from graph.workflow import build_graph

# Initialize graph
graph = build_graph()

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process chat message using LangGraph.
    Returns response with citations from retrieved documents.
    """
    logger.info(f"Received chat request: {request.message}")
    
    try:
        # Invoke the graph
        # We pass an empty history for this simple stateless demo, 
        # in a real app we'd fetch it from the DB.
        result = await graph.ainvoke({
            "input": request.message, 
            "chat_history": []
        })
        
        # Extract response
        final_response = result.get("final_response", "No response generated.")
        domain = result.get("domain", "general")
        tool_used = result.get("tool_name")
        citations = result.get("citations", [])
        
        # Convert Citation objects to dicts for JSON serialization
        # Use model_dump() for Pydantic v2, fallback to dict() for v1
        if citations:
            try:
                citations_list = [citation.model_dump() if hasattr(citation, 'model_dump') else citation.dict() for citation in citations]
            except:
                citations_list = [citation.dict() for citation in citations]
        else:
            citations_list = []
        
        return ChatResponse(
            response=final_response,
            session_id=request.session_id or "session_123",
            tool_used=tool_used if tool_used and tool_used != "none" else None,
            citations=citations_list,
            domain=domain
        )
    except Exception as e:
        logger.error(f"Error processing chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
