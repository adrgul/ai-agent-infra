"""Unit tests for VersionStore

Tests:
- Save/load version tracking
- Change detection
- Deletion
- Persistence across instances
"""
import pytest
from pathlib import Path
import tempfile

from rag.ingestion.version_store import VersionStore


def test_version_store_new_document():
    """Track a new document."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "versions.json"
        store = VersionStore(store_path)
        
        # Initially empty
        assert store.get_version("doc1") is None
        assert store.has_changed("doc1", "hash123")
        
        # Add document
        store.update("doc1", "hash123", "/path/to/doc1.pdf", 10)
        
        # Now tracked
        assert store.get_version("doc1") == "hash123"
        assert not store.has_changed("doc1", "hash123")


def test_version_store_change_detection():
    """Detect when document hash changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "versions.json"
        store = VersionStore(store_path)
        
        store.update("doc1", "hash_v1", "/path/to/doc1.pdf", 10)
        
        # Same hash => no change
        assert not store.has_changed("doc1", "hash_v1")
        
        # Different hash => changed
        assert store.has_changed("doc1", "hash_v2")


def test_version_store_persistence():
    """Version store persists across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "versions.json"
        
        # First instance
        store1 = VersionStore(store_path)
        store1.update("doc1", "hash123", "/path/doc1.pdf", 5)
        
        # Second instance (reload from disk)
        store2 = VersionStore(store_path)
        assert store2.get_version("doc1") == "hash123"


def test_version_store_removal():
    """Remove a document from tracking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "versions.json"
        store = VersionStore(store_path)
        
        store.update("doc1", "hash123", "/path/doc1.pdf", 5)
        assert store.get_version("doc1") == "hash123"
        
        store.remove("doc1")
        assert store.get_version("doc1") is None


def test_version_store_list_all():
    """List all tracked doc_ids."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "versions.json"
        store = VersionStore(store_path)
        
        store.update("doc1", "hash1", "/path/doc1.pdf", 5)
        store.update("doc2", "hash2", "/path/doc2.pdf", 3)
        
        doc_ids = store.get_all_doc_ids()
        assert set(doc_ids) == {"doc1", "doc2"}


def test_version_store_clear():
    """Clear all version data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store_path = Path(tmpdir) / "versions.json"
        store = VersionStore(store_path)
        
        store.update("doc1", "hash1", "/path/doc1.pdf", 5)
        store.update("doc2", "hash2", "/path/doc2.pdf", 3)
        
        store.clear()
        assert len(store.get_all_doc_ids()) == 0
