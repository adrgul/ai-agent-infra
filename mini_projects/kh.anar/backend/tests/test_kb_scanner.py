"""Unit tests for file scanner

Tests:
- File hash determinism
- Change detection
- Folder scanning with multiple file types
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from rag.ingestion.scanner import compute_file_hash, scan_kb_folder


def test_file_hash_deterministic():
    """Same content => same hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "test.txt"
        fpath.write_text("Hello World", encoding="utf-8")
        
        hash1 = compute_file_hash(fpath)
        hash2 = compute_file_hash(fpath)
        
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256


def test_file_hash_change_detection():
    """Different content => different hash."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fpath = Path(tmpdir) / "test.txt"
        
        fpath.write_text("Version 1", encoding="utf-8")
        hash1 = compute_file_hash(fpath)
        
        fpath.write_text("Version 2", encoding="utf-8")
        hash2 = compute_file_hash(fpath)
        
        assert hash1 != hash2


def test_scan_kb_folder_empty():
    """Empty folder => no documents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir)
        docs = scan_kb_folder(kb_dir)
        assert docs == []


def test_scan_kb_folder_pdf():
    """Scan folder with PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir)
        pdf_file = kb_dir / "guide.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake content")
        
        docs = scan_kb_folder(kb_dir, extensions=[".pdf"])
        
        assert len(docs) == 1
        assert docs[0]["doc_id"] == "guide.pdf"
        assert docs[0]["extension"] == ".pdf"
        assert docs[0]["file_size"] > 0
        assert len(docs[0]["version_hash"]) == 64


def test_scan_kb_folder_multiple_types():
    """Scan folder with multiple file types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir)
        
        (kb_dir / "doc1.pdf").write_bytes(b"%PDF-1.4 content")
        (kb_dir / "doc2.txt").write_text("Text content", encoding="utf-8")
        (kb_dir / "doc3.md").write_text("# Markdown", encoding="utf-8")
        (kb_dir / "ignored.docx").write_text("Should be ignored", encoding="utf-8")
        
        docs = scan_kb_folder(kb_dir, extensions=[".pdf", ".txt", ".md"])
        
        assert len(docs) == 3
        doc_ids = {d["doc_id"] for d in docs}
        assert doc_ids == {"doc1.pdf", "doc2.txt", "doc3.md"}


def test_scan_kb_folder_nested():
    """Scan nested folder structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_dir = Path(tmpdir)
        subdir = kb_dir / "subdir"
        subdir.mkdir()
        
        (kb_dir / "root.pdf").write_bytes(b"%PDF")
        (subdir / "nested.pdf").write_bytes(b"%PDF")
        
        docs = scan_kb_folder(kb_dir, extensions=[".pdf"])
        
        assert len(docs) == 2
        doc_ids = {d["doc_id"] for d in docs}
        # doc_id should reflect relative path
        assert "root.pdf" in doc_ids
        assert "subdir_nested.pdf" in doc_ids  # / replaced with _
