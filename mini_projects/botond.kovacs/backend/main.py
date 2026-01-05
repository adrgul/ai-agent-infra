from fastapi import FastAPI, HTTPException
from services.user_profile import UserProfileService, UserProfile
from services.conversation_history import ConversationHistoryService
from services.langgraph_workflow import create_langgraph_workflow
import logging

app = FastAPI()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backend.log")
    ]
)

# Initialize user profile service
user_profile_service = UserProfileService()

# Initialize conversation history service
conversation_history_service = ConversationHistoryService()

# Initialize LangGraph workflow
langgraph_workflow = create_langgraph_workflow()

@app.middleware("http")
async def log_requests(request, call_next):
    logging.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logging.info(f"Response status: {response.status_code}")
    return response

@app.get("/")
def read_root():
    return {"message": "Backend is running!"}

@app.get("/api/profile/{user_id}")
def get_user_profile(user_id: str):
    try:
        profile = user_profile_service.load_or_create_user_profile(user_id)
        return profile.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/profile/{user_id}")
def update_user_profile(user_id: str, updates: dict):
    try:
        profile = user_profile_service.update_user_profile(user_id, updates)
        return profile.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}")
def get_session_history(session_id: str, limit: int = None):
    try:
        messages = conversation_history_service.get_messages(session_id, limit)
        return {"session_id": session_id, "messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
def chat(user_id: str, message: str):
    try:
        if message.strip().lower() == "reset context":
            # Reset context
            conversation_history_service.save_session(user_id, {"messages": []})
            user_profile = user_profile_service.load_or_create_user_profile(user_id)
            return {
                "final_answer": "Context has been reset. Your preferences are preserved.",
                "tools_used": [],
                "memory_snapshot": {
                    "preferences": user_profile.dict(),
                    "workflow_state": {}
                }
            }
        else:
            # Normal chat flow (to be implemented later)
            return {"message": "Chat functionality is under construction."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))