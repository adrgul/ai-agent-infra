import json
import os
from pathlib import Path
from ...domain.ports import HistoryPort
from ...config.settings import settings


class FileHistoryRepository(HistoryPort):
    def __init__(self):
        self.data_dir = Path(settings.data_dir)
        self.history_file = self.data_dir / "history.json"
        self.data_dir.mkdir(exist_ok=True)

    async def save_briefing(self, briefing_data: dict) -> None:
        """Save briefing with atomic write (temp file + rename)."""
        history = await self.get_history(limit=settings.max_history_entries - 1)
        history.insert(0, briefing_data)
        
        # Atomic write
        temp_file = self.data_dir / "history.json.tmp"
        try:
            with open(temp_file, "w") as f:
                json.dump(history, f, indent=2, default=str)
            temp_file.replace(self.history_file)
        except Exception:
            if temp_file.exists():
                temp_file.unlink()
            raise

    async def get_history(self, limit: int) -> list[dict]:
        """Retrieve briefing history."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, "r") as f:
                history = json.load(f)
            return history[:limit]
        except Exception:
            return []
