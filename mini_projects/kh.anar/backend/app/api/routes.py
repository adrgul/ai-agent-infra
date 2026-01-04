from fastapi import APIRouter, HTTPException

from ..models.schemas import ChatRequest, ChatResponse, DebugInfo
from ..services.agent import AgentOrchestrator
from ..services.storage import FileStorage

router = APIRouter()
storage = FileStorage()
agent = AgentOrchestrator()



@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    storage.load_profile(request.user_id)  # ensure profile exists

    if request.message.strip().lower() == "reset context":
        storage.reset_conversation(request.user_id, request.session_id)
        debug = DebugInfo(
            request_json=request.model_dump(),
            user_id=request.user_id,
            session_id=request.session_id,
            user_query=request.message,
            rag_context=[],
            final_llm_prompt="reset context invoked - no LLM call",
        )
        return ChatResponse(
            reply="Conversation history cleared for this session.",
            user_id=request.user_id,
            session_id=request.session_id,
            history=[],
            debug=debug,
        )

    history = storage.get_history(request.user_id, request.session_id)
    state = {
        "user_id": request.user_id,
        "session_id": request.session_id,
        "query": request.message,
        "history": history,
        "rag_context": [],
        "request_metadata": request.metadata,
    }

    result_state = await agent.run(state)
    reply = result_state.get("response_text", "")

    user_record = storage.append_message(
        request.user_id, request.session_id, "user", request.message, request.metadata
    )
    assistant_record = storage.append_message(
        request.user_id,
        request.session_id,
        "assistant",
        reply,
        {"rag_context": result_state.get("rag_context", [])},
    )

    response_history = history + [user_record, assistant_record]

    debug = DebugInfo(
        request_json=request.model_dump(),
        user_id=request.user_id,
        session_id=request.session_id,
        user_query=request.message,
        rag_context=result_state.get("rag_context", []),
        final_llm_prompt=result_state.get("final_prompt", ""),
    )

    return ChatResponse(
        reply=reply,
        user_id=request.user_id,
        session_id=request.session_id,
        history=response_history,
        debug=debug,
    )
