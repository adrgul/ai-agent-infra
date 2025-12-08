"""File-based history repository implementation."""
import asyncio
import json
from pathlib import Path
from typing import Any

from loguru import logger

from app.domain.models import HistoryEntry


class FileHistoryRepository:
    """History repository using JSON file storage."""

    def __init__(self, data_dir: Path):
        """
        Initialize file history repository.

        Args:
            data_dir: Directory for data persistence
        """
        self.data_dir = data_dir
        self.history_file = data_dir / "history.json"
        self._lock = asyncio.Lock()

    async def _read_history(self) -> list[dict[str, Any]]:
        """Read history from file."""
        if not self.history_file.exists():
            return []

        try:
            content = await asyncio.to_thread(self.history_file.read_text)
            return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to read history file: {e}")
            return []

    async def _write_history(self, history: list[dict[str, Any]]) -> None:
        """Write history to file atomically."""
        try:
            content = json.dumps(history, indent=2, default=str)
            # Atomic write: write to temp file, then rename
            temp_file = self.history_file.with_suffix(".tmp")
            await asyncio.to_thread(temp_file.write_text, content)
            await asyncio.to_thread(temp_file.replace, self.history_file)
        except IOError as e:
            logger.error(f"Failed to write history file: {e}")
            raise

    async def add_entry(self, entry: HistoryEntry) -> None:
        """
        Add a history entry.

        Args:
            entry: History entry to add
        """
        async with self._lock:
            history = await self._read_history()
            
            # Add new entry
            history.append(entry.model_dump(mode="json"))
            
            # Keep only last 20 entries
            if len(history) > 20:
                history = history[-20:]
            
            await self._write_history(history)
            
            logger.debug(f"Added history entry: {entry.city} on {entry.date}")

    async def get_recent(self, limit: int = 20) -> list[HistoryEntry]:
        """
        Get recent history entries.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of recent history entries
        """
        async with self._lock:
            history = await self._read_history()
            
            # Return most recent entries
            recent = history[-limit:] if len(history) > limit else history
            
            # Reverse to show most recent first
            recent.reverse()
            
            return [HistoryEntry(**item) for item in recent]
