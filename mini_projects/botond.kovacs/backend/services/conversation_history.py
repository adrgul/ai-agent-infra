import os
import json
from datetime import datetime
from typing import List, Dict

class ConversationHistoryService:
    def __init__(self, base_dir="data/sessions"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def get_session_path(self, session_id: str) -> str:
        return os.path.join(self.base_dir, f"{session_id}.json")

    def load_or_create_session(self, session_id: str) -> Dict:
        path = self.get_session_path(session_id)
        if os.path.exists(path):
            with open(path, "r") as file:
                return json.load(file)
        else:
            session = {"messages": []}
            self.save_session(session_id, session)
            return session

    def save_session(self, session_id: str, session_data: Dict):
        path = self.get_session_path(session_id)
        with open(path, "w") as file:
            json.dump(session_data, file, indent=4)

    def append_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        session = self.load_or_create_session(session_id)
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        session["messages"].append(message)
        self.save_session(session_id, session)

    def get_messages(self, session_id: str, limit: int = None) -> List[Dict]:
        session = self.load_or_create_session(session_id)
        messages = session.get("messages", [])
        if limit:
            return messages[-limit:]
        return messages