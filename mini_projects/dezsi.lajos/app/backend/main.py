import os
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from domain.models import ChatRequest, ChatResponse
from infrastructure.repositories import InMemConversationRepository
from infrastructure.tool_clients import GeminiClient, QdrantVectorDB, RestTicketClient
from services.agent import TriageAgent
from services.chat_service import ChatService

# Load Env
load_dotenv()

app = FastAPI(title="Medical Support AI Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DI Container (Simple Singleton for Demo)
class Container:
    def __init__(self):
        self.repo = InMemConversationRepository()
        self.llm_client = GeminiClient()
        self.vector_db = QdrantVectorDB() # Will create local DB
        
        # Ticket System Config
        ticket_url = os.getenv("TICKET_SYSTEM_URL", "http://localhost:9000/api")
        ticket_key = os.getenv("TICKET_SYSTEM_API_KEY", "")
        self.ticket_client = RestTicketClient(base_url=ticket_url, api_key=ticket_key)
        
        self.agent = TriageAgent(self.llm_client, self.vector_db, self.ticket_client)
        self.chat_service = ChatService(self.agent, self.repo)

container = Container()

def get_chat_service():
    return container.chat_service

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Medical Support AI Agent API",
        "docs": "/docs",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: ChatService = Depends(get_chat_service)):
    conv_id = request.conversation_id or str(uuid.uuid4())
    return await service.process_message(conv_id, request.message)

@app.get("/history/{conversation_id}")
async def get_history(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    return await service.get_history(conversation_id)

@app.post("/reset/{conversation_id}")
async def reset_context(conversation_id: str, service: ChatService = Depends(get_chat_service)):
    await service.clear_history(conversation_id)
    return {"status": "cleared"}

@app.get("/debug/conversations")
async def list_conversations():
    """Debug endpoint to list all active conversation IDs in memory."""
    repo = container.repo
    # Accessing private attribute for debug purposes
    if hasattr(repo, "_conversations"):
         return {"active_conversations": list(repo._conversations.keys())}
    return {"active_conversations": []}

@app.post("/seed_kb")
async def seed_kb():
    """
    Seed the vector DB with policies from the knowledge base directory.
    Generates PDFs if they don't exist, then ingests them.
    """
    db = container.vector_db
    
    # 1. Generate KB if needed
    kb_dir = os.path.join(os.path.dirname(__file__), "knowledge_base")
    script_path = os.path.join(os.path.dirname(__file__), "scripts", "generate_kb.py")
    
    if not os.path.exists(kb_dir) or not os.listdir(kb_dir):
        print("DEBUG: Generating Knowledge Base PDFs...")
        import subprocess
        try:
            subprocess.run(["python", script_path], check=True)
        except Exception as e:
            print(f"ERROR running generation script: {e}")
            return {"status": "error", "message": "Failed to generate PDFs. Please ensure dependencies are installed."}

    # 2. Ingest
    ingested_count = 0
    chunks_count = 0
    if os.path.exists(kb_dir):
        files = [f for f in os.listdir(kb_dir) if f.endswith(".pdf") or f.endswith(".txt")]
        for f in files:
            path = os.path.join(kb_dir, f)
            # Default tenant_id for demo. In prod, this would come from an admin API or config.
            # Using multiple tenants to show capability
            tenant = "tenant_a" if "Tier_1" in f else "tenant_b" # Just to demo separation
            
            # Use 'default' or a specific tenant for general documents
            tenant = "default" 
            
            count = await db.ingest_document(path, tenant_id=tenant)
            chunks_count += count
            ingested_count += 1
            
    return {"status": "seeded", "files_ingested": ingested_count, "total_chunks": chunks_count}

# Instructions for developer (as requested)
"""
Usage Instructions:
1. Copy .env.example to .env and set GOOGLE_API_KEY.
2. Build Docker: docker build -t medical-ai-agent .
3. Run Docker: docker run -p 8000:8000 --env-file .env medical-ai-agent
"""
