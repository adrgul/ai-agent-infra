import json
from pathlib import Path
from typing import Dict, List

from ..core.config import settings
from ..models.schemas import MessageRecord, UserProfile


class FileStorage:
    """Filesystem persistence for users and conversations."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.data_dir
        self.conversations_dir = self.base_dir / "conversations"
        self.users_dir = self.base_dir / "users"
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.users_dir.mkdir(parents=True, exist_ok=True)

    def _conversation_dir(self, user_id: str, session_id: str) -> Path:
        path = self.conversations_dir / user_id / session_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _user_profile_path(self, user_id: str) -> Path:
        return self.users_dir / f"{user_id}.json"

    def load_profile(self, user_id: str) -> UserProfile:
        profile_path = self._user_profile_path(user_id)
        if profile_path.exists():
            data = json.loads(profile_path.read_text())
            return UserProfile(**data)

        profile = UserProfile(user_id=user_id)
        self.save_profile(profile)
        return profile

    def save_profile(self, profile: UserProfile) -> None:
        profile.touch()
        path = self._user_profile_path(profile.user_id)
        path.write_text(profile.model_dump_json(indent=2))

    def append_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Dict | None = None,
    ) -> MessageRecord:
        record = MessageRecord(role=role, content=content, metadata=metadata or {})
        directory = self._conversation_dir(user_id, session_id)
        filename = f"{record.timestamp.strftime('%Y%m%dT%H%M%S%f')}_{role}.json"
        (directory / filename).write_text(record.model_dump_json(indent=2))
        return record

    def get_history(self, user_id: str, session_id: str) -> List[MessageRecord]:
        directory = self._conversation_dir(user_id, session_id)
        records: List[MessageRecord] = []
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text())
                records.append(MessageRecord(**data))
            except json.JSONDecodeError:
                continue
        return records

    def reset_conversation(self, user_id: str, session_id: str) -> None:
        directory = self._conversation_dir(user_id, session_id)
        for path in directory.glob("*.json"):
            path.unlink(missing_ok=True)
