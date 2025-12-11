"""
Services - Chat service orchestration.
"""
import logging
from typing import Optional, Dict, Any
from uuid import uuid4

from domain.models import QueryRequest, QueryResponse, UserProfile, Message
from domain.interfaces import IUserRepository, IConversationRepository
from services.agent import QueryAgent

logger = logging.getLogger(__name__)


class ChatService:
    """Orchestrates chat workflow with persistence."""

    def __init__(
        self,
        user_repo: IUserRepository,
        conversation_repo: IConversationRepository,
        agent: QueryAgent,
    ):
        self.user_repo = user_repo
        self.conversation_repo = conversation_repo
        self.agent = agent

    async def process_query(self, request: QueryRequest) -> QueryResponse:
        """Process user query through agent workflow."""
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid4())

        # Special command: reset context
        if request.query.strip().lower() == "reset context":
            await self.conversation_repo.clear_history(session_id)
            logger.info(f"Context reset for session={session_id}")
            
            return QueryResponse(
                domain="general",
                answer="Kontextus visszaállítva. Új beszélgetést kezdünk, de a beállítások megmaradnak.",
                citations=[],
                workflow={"action": "reset_context", "status": "completed"}
            )

        # Load user profile
        user_profile = await self.user_repo.get_profile(request.user_id)

        # Load conversation history
        history = await self.conversation_repo.get_history(session_id)

        # Save user message
        user_message = Message(role="user", content=request.query)
        await self.conversation_repo.save_message(session_id, user_message)

        # Run agent
        response = await self.agent.run(
            query=request.query,
            user_id=request.user_id,
            session_id=session_id,
        )

        # Save assistant message
        assistant_message = Message(
            role="assistant",
            content=response.answer,
            metadata={
                "domain": response.domain,
                "citations": [c.model_dump() for c in response.citations],
            }
        )
        await self.conversation_repo.save_message(session_id, assistant_message)

        logger.info(f"Query processed: user={request.user_id}, domain={response.domain}")

        return response

    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get conversation history for a session."""
        messages = await self.conversation_repo.get_history(session_id)
        return {
            "session_id": session_id,
            "messages": [m.model_dump(mode='json') for m in messages],
            "count": len(messages),
        }

    async def search_history(self, query: str) -> list:
        """Search conversation history."""
        results = await self.conversation_repo.search_messages(query)
        return [
            {
                "role": r.role,
                "content": r.content[:100],
                "timestamp": r.timestamp.isoformat(),
            }
            for r in results[:20]
        ]
