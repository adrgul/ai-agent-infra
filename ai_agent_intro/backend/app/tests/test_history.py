"""Tests for file-based history repository."""
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from app.domain.models import HistoryEntry
from app.infrastructure.persistence.file_history import FileHistoryRepository


@pytest.mark.asyncio
async def test_add_and_get_history():
    """Test adding and retrieving history entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileHistoryRepository(Path(tmpdir))

        # Add entries
        entry1 = HistoryEntry(
            city="Budapest", date=date(2025, 11, 18), timestamp=datetime.utcnow()
        )
        entry2 = HistoryEntry(
            city="Prague", date=date(2025, 11, 19), timestamp=datetime.utcnow()
        )

        await repo.add_entry(entry1)
        await repo.add_entry(entry2)

        # Retrieve
        history = await repo.get_recent()

        assert len(history) == 2
        # Most recent first
        assert history[0].city == "Prague"
        assert history[1].city == "Budapest"


@pytest.mark.asyncio
async def test_history_limit():
    """Test history entry limit (max 20)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileHistoryRepository(Path(tmpdir))

        # Add 25 entries
        for i in range(25):
            entry = HistoryEntry(
                city=f"City{i}", date=date(2025, 11, 18), timestamp=datetime.utcnow()
            )
            await repo.add_entry(entry)

        # Should only keep last 20
        history = await repo.get_recent()

        assert len(history) == 20
        # Most recent should be City24
        assert history[0].city == "City24"
        # Oldest should be City5 (entries 0-4 were dropped)
        assert history[-1].city == "City5"


@pytest.mark.asyncio
async def test_empty_history():
    """Test retrieving history when empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = FileHistoryRepository(Path(tmpdir))

        history = await repo.get_recent()

        assert len(history) == 0


@pytest.mark.asyncio
async def test_history_persistence():
    """Test that history persists across repository instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)

        # Create first repo and add entry
        repo1 = FileHistoryRepository(data_dir)
        entry = HistoryEntry(
            city="Budapest", date=date(2025, 11, 18), timestamp=datetime.utcnow()
        )
        await repo1.add_entry(entry)

        # Create second repo and read
        repo2 = FileHistoryRepository(data_dir)
        history = await repo2.get_recent()

        assert len(history) == 1
        assert history[0].city == "Budapest"
