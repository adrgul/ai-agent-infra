"""
Service layer - Chat service implementing business logic.
Following SOLID: 
- Single Responsibility - Handles chat workflow coordination.
- Dependency Inversion - Depends on repository and agent abstractions.
"""
from typing import Dict, Any, List
import logging
from datetime import datetime

from domain.models import (
    Message, Memory, WorkflowState, ChatRequest, ChatResponse,
    UserProfile, ConversationHistory
)
from domain.interfaces import IUserRepository, IConversationRepository
from services.agent import AIAgent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

logger = logging.getLogger(__name__)


class ChatService:
    """
    Chat service coordinating the full chat workflow:
    1. Load/create user profile and conversation history
    2. Handle special commands (e.g., "reset context")
    3. Build memory context
    4. Run agent
    5. Persist all messages and updates
    """
    
    def __init__(
        self,
        user_repository: IUserRepository,
        conversation_repository: IConversationRepository,
        agent: AIAgent
    ):
        self.user_repo = user_repository
        self.conversation_repo = conversation_repository
        self.agent = agent
    
    async def process_message(self, request: ChatRequest) -> ChatResponse:
        """
        Process incoming chat message.
        
        Workflow:
        1. Check for special commands (reset context)
        2. Load user profile and conversation history
        3. Build memory context
        4. Add user message to history
        5. Run agent
        6. Persist assistant messages and updates
        7. Return response
        """
        user_id = request.user_id
        session_id = request.session_id or user_id
        message = request.message.strip()
        
        logger.info(f"Processing message from user {user_id}, session {session_id}")
        
        # Check for reset context command
        if message.lower() == "reset context":
            return await self._handle_reset_context(user_id, session_id)
        
        # Load user profile (creates if doesn't exist)
        profile = await self.user_repo.get_profile(user_id)
        
        # Load conversation history (creates if doesn't exist)
        history = await self.conversation_repo.get_history(session_id)
        
        # Build memory context
        memory = self._build_memory(profile, history)
        
        # Add user message to history
        user_msg = Message(role="user", content=message, timestamp=datetime.now())
        await self.conversation_repo.add_message(session_id, user_msg)
        
        # Run agent
        agent_result = await self.agent.run(
            user_message=message,
            memory=memory,
            user_id=user_id
        )
        
        # Extract results
        final_answer = agent_result["final_answer"]
        tools_called = agent_result["tools_called"]
        agent_messages = agent_result["messages"]
        
        # Persist all messages from agent (system messages, tool messages, assistant message)
        for msg in agent_messages:
            if isinstance(msg, SystemMessage):
                await self.conversation_repo.add_message(
                    session_id,
                    Message(role="system", content=msg.content, timestamp=datetime.now())
                )
            elif isinstance(msg, AIMessage):
                await self.conversation_repo.add_message(
                    session_id,
                    Message(role="assistant", content=msg.content, timestamp=datetime.now())
                )
        
        # Check if profile needs updating based on conversation
        await self._check_profile_updates(user_id, message, profile)
        
        # Reload profile to get any updates
        updated_profile = await self.user_repo.get_profile(user_id)
        
        # Build response
        tools_used = [
            {
                "name": tc.tool_name,
                "arguments": tc.arguments,
                "success": tc.error is None
            }
            for tc in tools_called
        ]
        
        memory_snapshot = {
            "preferences": {
                "language": updated_profile.language,
                "default_city": updated_profile.default_city,
                **updated_profile.preferences
            },
            "workflow_state": memory.workflow_state.model_dump(),
            "message_count": len(history.messages) + len(agent_messages)
        }
        
        logger.info(f"Message processed successfully for user {user_id}")
        
        return ChatResponse(
            final_answer=final_answer,
            tools_used=tools_used,
            memory_snapshot=memory_snapshot,
            logs=[f"Tools called: {len(tools_called)}"]
        )
    
    async def _handle_reset_context(self, user_id: str, session_id: str) -> ChatResponse:
        """
        Handle 'reset context' command.
        
        Behavior:
        - Clear conversation history
        - Keep user profile intact
        - Return confirmation message
        """
        logger.info(f"Resetting context for user {user_id}, session {session_id}")
        
        # Load profile (ensure it exists)
        profile = await self.user_repo.get_profile(user_id)
        
        # Clear conversation history
        await self.conversation_repo.clear_history(session_id)
        
        # Determine response language
        language = profile.language
        
        if language == "hu":
            message = "A kontextus törölve lett. Új beszélgetést kezdünk, de a beállításaid megmaradtak."
        else:
            message = "Context has been reset. We are starting a new conversation, but your preferences are preserved."
        
        # Add system message about reset
        reset_msg = Message(
            role="system",
            content=f"Context reset by user {user_id}",
            timestamp=datetime.now()
        )
        await self.conversation_repo.add_message(session_id, reset_msg)
        
        logger.info(f"Context reset completed for user {user_id}")
        
        return ChatResponse(
            final_answer=message,
            tools_used=[],
            memory_snapshot={
                "preferences": {
                    "language": profile.language,
                    "default_city": profile.default_city,
                    **profile.preferences
                },
                "workflow_state": WorkflowState().model_dump(),
                "message_count": 1
            },
            logs=["Context reset"]
        )
    
    def _build_memory(self, profile: UserProfile, history: ConversationHistory) -> Memory:
        """Build memory context from profile and history."""
        
        # Get recent messages for chat history (last 20)
        recent_messages = history.messages[-20:] if len(history.messages) > 20 else history.messages
        
        # Build preferences from profile
        preferences = {
            "language": profile.language,
            "default_city": profile.default_city,
            **profile.preferences
        }
        
        # Build workflow state (simplified for demo)
        workflow_state = WorkflowState()
        
        return Memory(
            chat_history=recent_messages,
            preferences=preferences,
            workflow_state=workflow_state
        )
    
    async def _check_profile_updates(self, user_id: str, message: str, profile: UserProfile) -> None:
        """
        Check if user message indicates profile preference changes.
        Simple heuristic-based detection for demo purposes.
        """
        message_lower = message.lower()
        
        updates = {}
        preferences_updates = {}
        
        # Language change detection
        if any(phrase in message_lower for phrase in ["answer in english", "válaszolj angolul", "use english"]):
            updates["language"] = "en"
        elif any(phrase in message_lower for phrase in ["answer in hungarian", "válaszolj magyarul", "use hungarian"]):
            updates["language"] = "hu"
        
        # City preference detection
        if "default city" in message_lower or "alapértelmezett város" in message_lower:
            # Simple extraction (in production, use NER)
            for city in ["budapest", "szeged", "debrecen", "pécs", "győr"]:
                if city in message_lower:
                    updates["default_city"] = city.capitalize()
                    break
        
        # Name detection - improved pattern matching
        import re
        
        # Try to extract name from common patterns
        name_patterns = [
            r"(?:my name is|call me|i am|i'm)\s+([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)",  # English
            r"(?:a nevem|hívnak|vagyok|én vagyok)\s+([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)",  # Hungarian
            r"([A-Z][a-záéíóöőúüű]+)\s+vagyok",  # "[Name] vagyok"
            r"(?:szia|hello|hi|helló)\s+([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)",  # "Szia [Name]" or "Hi [Name]"
            r"^([A-Z][a-záéíóöőúüű][a-záéíóöőúüű]+)\s+(?:here|itt|speaking)",  # "[Name] here/itt/speaking"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                potential_name = match.group(1).strip('.,!?')
                # Filter out common words that aren't names (but allow actual names to update)
                excluded_words = ['szia', 'hello', 'helló', 'hi', 'hey', 'hola', 'budapest', 'hogyan', 'segíthetek']
                if len(potential_name) > 1 and potential_name.lower() not in excluded_words:
                    preferences_updates["name"] = potential_name
                    logger.info(f"Detected name: {potential_name}")
                    break
        
        # Merge preferences updates
        if preferences_updates:
            current_prefs = profile.preferences.copy()
            current_prefs.update(preferences_updates)
            updates["preferences"] = current_prefs
        
        if updates:
            await self.user_repo.update_profile(user_id, updates)
            logger.info(f"Updated profile for user {user_id}: {updates}")
    
    async def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """Get session history."""
        history = await self.conversation_repo.get_history(session_id)
        
        return {
            "session_id": session_id,
            "messages": [msg.model_dump(mode='json') for msg in history.messages],
            "summary": history.summary,
            "created_at": history.created_at.isoformat(),
            "updated_at": history.updated_at.isoformat()
        }
    
    async def search_history(self, query: str) -> List[Dict[str, Any]]:
        """Search across all conversation histories."""
        results = await self.conversation_repo.search_messages(query)
        
        return [
            {
                "session_id": r.session_id,
                "snippet": r.snippet,
                "timestamp": r.timestamp.isoformat(),
                "role": r.role
            }
            for r in results
        ]
