"""
Infrastructure - File-based repositories and API clients.
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from domain.models import Message, UserProfile, Citation
from domain.interfaces import IUserRepository, IConversationRepository

logger = logging.getLogger(__name__)


class FileUserRepository(IUserRepository):
    """File-based user profile storage (JSON)."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, user_id: str) -> Path:
        return self.data_dir / f"{user_id}.json"

    async def get_profile(self, user_id: str) -> UserProfile:
        """Load user profile or create default."""
        filepath = self._get_filepath(user_id)
        
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return UserProfile(**data)
        
        # Create default profile
        profile = UserProfile(user_id=user_id, organisation="Default Org")
        await self.save_profile(profile)
        return profile

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        """Save user profile to file."""
        filepath = self._get_filepath(profile.user_id)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile.model_dump(mode='json'), f, indent=2, default=str)
        logger.info(f"Profile saved: {profile.user_id}")
        return profile

    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Update user profile with new data."""
        profile = await self.get_profile(user_id)
        
        for key, value in updates.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        profile.updated_at = datetime.now()
        return await self.save_profile(profile)


class FileConversationRepository(IConversationRepository):
    """File-based conversation history storage (JSON)."""

    def __init__(self, data_dir: Path):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_filepath(self, session_id: str) -> Path:
        return self.data_dir / f"{session_id}.json"

    async def get_history(self, session_id: str) -> List[Message]:
        """Load conversation history."""
        filepath = self._get_filepath(session_id)
        
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Message(**msg) for msg in data.get("messages", [])]
        
        return []

    async def save_message(self, session_id: str, message: Message) -> None:
        """Append message to session history."""
        filepath = self._get_filepath(session_id)
        
        # Load existing or create new
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {"session_id": session_id, "messages": [], "created_at": datetime.now().isoformat()}
        
        # Append message
        data["messages"].append(message.model_dump(mode='json'))
        data["updated_at"] = datetime.now().isoformat()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)

    async def clear_history(self, session_id: str) -> None:
        """Clear conversation history."""
        filepath = self._get_filepath(session_id)
        
        # Create new empty history
        data = {
            "session_id": session_id,
            "messages": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "cleared_at": datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"History cleared: {session_id}")

    async def search_messages(self, query: str) -> List[Message]:
        """Search across all messages."""
        results = []
        query_lower = query.lower()
        
        for filepath in self.data_dir.glob("*.json"):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for msg_data in data.get("messages", []):
                if query_lower in msg_data.get("content", "").lower():
                    msg = Message(**msg_data)
                    results.append(msg)
        
        return results
