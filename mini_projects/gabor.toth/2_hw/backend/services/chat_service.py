"""Chat service orchestrating message flow."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from domain.models import Message, MessageRole, UserProfile
from domain.interfaces import (
    UserProfileRepository, SessionRepository, ActivityCallback
)
from services.rag_agent import RAGAgent


class ChatService:
    """Service for handling chat interactions."""

    def __init__(
        self,
        rag_agent: RAGAgent,
        profile_repo: UserProfileRepository,
        session_repo: SessionRepository,
        upload_repo=None,  # Optional file upload repo to get global categories
        activity_callback: Optional[ActivityCallback] = None,
    ):
        self.rag_agent = rag_agent
        self.profile_repo = profile_repo
        self.session_repo = session_repo
        self.upload_repo = upload_repo
        self.activity_callback = activity_callback

    async def process_message(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        Process user message:
        - Check for reset context command
        - Load/create profile
        - Append user message
        - Run RAG agent
        - Append assistant response
        - Return response
        """
        # Check for reset context command (case-insensitive)
        # Handle both "reset context" and the confirmation variant
        message_lower = user_message.strip().lower()
        if message_lower == "reset context" or message_lower.startswith("reset context ("):
            return await self._handle_reset_context(user_id, session_id)

        # Log: Message received
        if self.activity_callback:
            await self.activity_callback.log_activity(
                f"💬 Kérdés feldolgozása: '{user_message[:50]}{'...' if len(user_message) > 50 else ''}'",
                activity_type="processing"
            )

        # Load or create profile
        profile = await self.profile_repo.get_profile(user_id)
        if not profile:
            profile = UserProfile(user_id=user_id)
            await self.profile_repo.save_profile(profile)

        # Get available categories - now from upload repo (global, not user-specific)
        available_categories = []
        if self.upload_repo:
            available_categories = await self.upload_repo.get_categories()
        
        # If no categories uploaded, respond
        if not available_categories:
            response = {
                "final_answer": "Még nincsenek feltöltött dokumentumok. Kérjük, először töltsön fel egy dokumentumot egy kategóriához.",
                "tools_used": [],
                "memory_snapshot": {
                    "available_categories": [],
                }
            }
            # Append messages
            await self.session_repo.append_message(
                session_id,
                Message(
                    role=MessageRole.USER,
                    content=user_message,
                    timestamp=datetime.now(),
                )
            )
            await self.session_repo.append_message(
                session_id,
                Message(
                    role=MessageRole.ASSISTANT,
                    content=response["final_answer"],
                    timestamp=datetime.now(),
                    metadata={"response_type": "no_documents"},
                )
            )

            # Log: No documents
            if self.activity_callback:
                await self.activity_callback.log_activity(
                    "⚠️ Nincs feltöltött dokumentum",
                    activity_type="warning"
                )

            return response

        # Append user message
        await self.session_repo.append_message(
            session_id,
            Message(
                role=MessageRole.USER,
                content=user_message,
                timestamp=datetime.now(),
                user_id=user_id,
            )
        )

        # Log: Category routing
        if self.activity_callback:
            await self.activity_callback.log_activity(
                f"🎯 Kategória felismerés: {len(available_categories)} kategória közül",
                activity_type="processing",
                metadata={"category_count": len(available_categories), "categories": available_categories}
            )

        # Run RAG agent with available global categories
        rag_response = await self.rag_agent.answer_question(
            user_id, user_message, available_categories,
            activity_callback=self.activity_callback
        )

        # Extract answer and metadata
        final_answer = rag_response["final_answer"]
        routed_category = rag_response["memory_snapshot"].get("routed_category")
        context_chunks = rag_response["context_chunks"]
        fallback_search = rag_response.get("fallback_search", False)

        # Log: Response ready
        if self.activity_callback:
            await self.activity_callback.log_activity(
                f"✓ Válasz kész: {len(context_chunks)} chunk felhasználva",
                activity_type="success",
                metadata={
                    "chunk_count": len(context_chunks),
                    "category": routed_category,
                    "fallback_search": fallback_search
                }
            )

        # Append assistant response
        chunk_ids = [c.chunk_id for c in context_chunks]
        await self.session_repo.append_message(
            session_id,
            Message(
                role=MessageRole.ASSISTANT,
                content=final_answer,
                timestamp=datetime.now(),
                metadata={
                    "category_routed": routed_category,
                    "chunk_ids": chunk_ids,
                    "fallback_search": fallback_search,
                }
            )
        )

        return {
            "final_answer": final_answer,
            "tools_used": [],
            "fallback_search": fallback_search,
            "memory_snapshot": rag_response["memory_snapshot"],
            "rag_debug": {
                "retrieved": [
                    {
                        "chunk_id": c.chunk_id,
                        "distance": c.distance,
                        "snippet": c.snippet,
                        "metadata": c.metadata,
                        "content": c.content,  # Full content for modal display
                        "source_file": c.metadata.get("source_file", "Unknown"),
                        "section_title": c.metadata.get("section_title", ""),
                    }
                    for c in context_chunks
                ]
            }
        }

    async def _handle_reset_context(
        self, user_id: str, session_id: str
    ) -> Dict[str, Any]:
        """Clear session conversation history only."""
        await self.session_repo.clear_messages(session_id)

        # Get profile for categories
        profile = await self.profile_repo.get_profile(user_id)
        categories = profile.categories if profile else []

        return {
            "final_answer": "Kontextus törölve, tiszta lappal megyünk tovább.",
            "tools_used": [],
            "memory_snapshot": {
                "available_categories": categories,
            }
        }

    async def get_session_history(self, session_id: str) -> List[Message]:
        """Get conversation history for a session."""
        return await self.session_repo.get_messages(session_id)
