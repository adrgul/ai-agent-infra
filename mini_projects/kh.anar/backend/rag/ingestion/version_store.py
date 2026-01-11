"""Document Version Store for KB ingestion

Design rationale:
- SRP: Track document versions (doc_id -> version_hash) for incremental updates.
- Persistence: Simple JSON file; could be upgraded to SQLite/DB for scale.
- Atomic writes: Use temp file + rename to avoid corruption.

Why this approach:
- Enables incremental ingestion: only reindex changed docs.
- Tracks lifecycle: new, updated, removed.
- Minimal dependencies (just JSON + filesystem).

Schema:
{
  "doc_id": {
    "version_hash": "abc123...",
    "last_indexed": "2026-01-11T12:34:56",
    "file_path": "docs/kb-data/guide.pdf",
    "chunk_count": 42
  }
}
"""
from __future__ import annotations
from pathlib import Path
import json
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class VersionStore:
    """Persistent store for document version tracking.
    
    Design notes:
    - Load/save via JSON for simplicity.
    - Atomic writes prevent corruption.
    - Thread-safe for single-process use (no multi-process locking).
    """
    
    def __init__(self, store_path: Path):
        self.store_path = store_path
        self._data: Dict[str, Dict[str, Any]] = {}
        self._load()
    
    def _load(self) -> None:
        """Load version data from disk."""
        if self.store_path.exists():
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
                logger.info(f"Loaded version store: {len(self._data)} documents")
            except Exception as e:
                logger.error(f"Failed to load version store: {e}")
                self._data = {}
        else:
            logger.info("Version store does not exist; starting fresh")
    
    def _save(self) -> None:
        """Save version data to disk atomically."""
        try:
            # Write to temp file first
            with tempfile.NamedTemporaryFile("w", delete=False, dir=str(self.store_path.parent), encoding="utf-8") as tf:
                json.dump(self._data, tf, indent=2, ensure_ascii=False)
                tmp_path = tf.name
            
            # Atomic rename
            Path(tmp_path).replace(self.store_path)
            logger.debug(f"Saved version store: {len(self._data)} documents")
        except Exception as e:
            logger.error(f"Failed to save version store: {e}")
    
    def get_version(self, doc_id: str) -> Optional[str]:
        """Get the version_hash for a document, or None if not tracked."""
        entry = self._data.get(doc_id)
        return entry["version_hash"] if entry else None
    
    def has_changed(self, doc_id: str, new_hash: str) -> bool:
        """Check if a document has changed (new or updated).
        
        Returns:
            True if doc is new or hash differs; False if unchanged.
        """
        old_hash = self.get_version(doc_id)
        return old_hash is None or old_hash != new_hash
    
    def update(self, doc_id: str, version_hash: str, file_path: str, chunk_count: int) -> None:
        """Update version info for a document."""
        self._data[doc_id] = {
            "version_hash": version_hash,
            "last_indexed": datetime.now(timezone.utc).isoformat(),
            "file_path": file_path,
            "chunk_count": chunk_count,
        }
        self._save()
    
    def remove(self, doc_id: str) -> None:
        """Remove a document from version tracking."""
        if doc_id in self._data:
            del self._data[doc_id]
            self._save()
    
    def get_all_doc_ids(self) -> list[str]:
        """Return all tracked doc_ids."""
        return list(self._data.keys())
    
    def clear(self) -> None:
        """Clear all version data (for full reindex)."""
        self._data = {}
        self._save()
