"""File Scanner for KB ingestion

Design rationale:
- SRP: This module's single responsibility is discovering files in the KB folder
  and computing stable identifiers (doc_id, version_hash) for change detection.
- Deterministic: File hash (SHA256) ensures we detect content changes reliably.
- Testable: Pure functions take paths and return metadata; no side effects.

Why hashing:
- Allows incremental updates: only re-index changed documents.
- Stable across runs: same file content => same hash => skip reindex.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
import hashlib
import logging

logger = logging.getLogger(__name__)


def compute_file_hash(path: Path) -> str:
    """Compute SHA256 hash of file content for version detection.
    
    Why SHA256: Strong collision resistance, widely supported, fast enough
    for typical KB documents (PDFs usually < 10MB).
    """
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            sha.update(chunk)
    return sha.hexdigest()


def scan_kb_folder(kb_dir: Path, extensions: List[str] = None) -> List[Dict[str, Any]]:
    """Scan the KB folder and return metadata for each discovered file.
    
    Args:
        kb_dir: Path to the KB data directory
        extensions: List of file extensions to include (e.g., [".pdf", ".txt", ".md"])
                   If None, defaults to [".pdf", ".txt", ".md"]
    
    Returns:
        List of dicts with keys: doc_id, file_path, version_hash, file_size, extension
    
    Design notes:
    - doc_id is derived from relative path (stable across moves within kb-data)
    - version_hash allows detecting file updates
    - We log discovery stats for observability
    """
    if extensions is None:
        extensions = [".pdf", ".txt", ".md"]
    
    if not kb_dir.exists():
        logger.warning(f"KB folder does not exist: {kb_dir}")
        return []
    
    discovered = []
    for ext in extensions:
        for fpath in kb_dir.rglob(f"*{ext}"):
            if not fpath.is_file():
                continue
            
            # Derive doc_id from relative path (replace / with _)
            # Why: stable identifier; allows organizing docs in subfolders
            relative = fpath.relative_to(kb_dir)
            doc_id = str(relative).replace("/", "_").replace("\\", "_")
            
            version_hash = compute_file_hash(fpath)
            
            discovered.append({
                "doc_id": doc_id,
                "file_path": str(fpath),
                "version_hash": version_hash,
                "file_size": fpath.stat().st_size,
                "extension": ext,
            })
    
    logger.info(f"Scanned {kb_dir}: found {len(discovered)} documents")
    return discovered
