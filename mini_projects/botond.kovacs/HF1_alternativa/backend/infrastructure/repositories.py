"""
Infrastructure layer - File-based repository implementations.
Following SOLID: Single Responsibility - each repository handles one type of data.
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from domain.models import UserProfile, ConversationHistory, Message, SearchResult
from domain.interfaces import IUserRepository, IConversationRepository
import logging

logger = logging.getLogger(__name__)


class FileUserRepository(IUserRepository):
    """File-based user profile repository."""
    
    def __init__(self, data_dir: str = "data/users"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}.json"
    
    async def get_profile(self, user_id: str) -> UserProfile:
        """Load or create user profile."""
        file_path = self._get_file_path(user_id)
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded profile for user {user_id}")
                    return UserProfile(**data)
            except Exception as e:
                logger.error(f"Error loading profile for {user_id}: {e}")
                # Fall through to create new profile
        
        # Create new profile with defaults
        profile = UserProfile(user_id=user_id)
        await self.save_profile(profile)
        logger.info(f"Created new profile for user {user_id}")
        return profile
    
    async def save_profile(self, profile: UserProfile) -> None:
        """Save user profile to storage."""
        profile.updated_at = datetime.now()
        file_path = self._get_file_path(profile.user_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved profile for user {profile.user_id}")
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update specific fields of user profile."""
        profile = await self.get_profile(user_id)
        
        # Update allowed fields
        if "language" in updates:
            profile.language = updates["language"]
        if "default_city" in updates:
            profile.default_city = updates["default_city"]
        if "preferences" in updates:
            profile.preferences.update(updates["preferences"])
        
        await self.save_profile(profile)
        logger.info(f"Updated profile for user {user_id}: {updates}")
        return profile


class FileConversationRepository(IConversationRepository):
    """File-based conversation history repository."""
    
    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, session_id: str) -> Path:
        return self.data_dir / f"{session_id}.json"
    
    async def get_history(self, session_id: str) -> ConversationHistory:
        """Load or create conversation history."""
        file_path = self._get_file_path(session_id)
        
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded history for session {session_id}")
                    return ConversationHistory(**data)
            except Exception as e:
                logger.error(f"Error loading history for {session_id}: {e}")
                # Fall through to create new history
        
        # Create new conversation history
        history = ConversationHistory(session_id=session_id)
        await self.save_history(history)
        logger.info(f"Created new history for session {session_id}")
        return history
    
    async def save_history(self, history: ConversationHistory) -> None:
        """Save conversation history to storage."""
        history.updated_at = datetime.now()
        file_path = self._get_file_path(history.session_id)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(history.model_dump(mode='json'), f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved history for session {history.session_id}")
    
    async def add_message(self, session_id: str, message: Message) -> None:
        """Append a message to conversation history."""
        history = await self.get_history(session_id)
        history.messages.append(message)
        await self.save_history(history)
        logger.info(f"Added {message.role} message to session {session_id}")
    
    async def clear_history(self, session_id: str) -> None:
        """Clear conversation history (reset context)."""
        history = ConversationHistory(session_id=session_id)
        await self.save_history(history)
        logger.info(f"Cleared history for session {session_id}")
    
    async def search_messages(self, query: str) -> List[SearchResult]:
        """Search across all conversations."""
        results = []
        query_lower = query.lower()
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    history = ConversationHistory(**data)
                    
                    for msg in history.messages:
                        if query_lower in msg.content.lower():
                            # Create snippet with context
                            snippet = msg.content[:200] + ("..." if len(msg.content) > 200 else "")
                            results.append(SearchResult(
                                session_id=history.session_id,
                                snippet=snippet,
                                timestamp=msg.timestamp,
                                role=msg.role
                            ))
            except Exception as e:
                logger.error(f"Error searching file {file_path}: {e}")
        
        logger.info(f"Search for '{query}' found {len(results)} results")
        return results
