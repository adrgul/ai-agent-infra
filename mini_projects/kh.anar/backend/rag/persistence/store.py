"""Simple JSON-backed DocumentStore

Design notes / why:
- Keeps documents persisted on disk under DATA_DIR/rag_documents.
- Files are written atomically (tmp write + rename) to avoid partial writes.
- Interface is minimal: save, load, list, delete — suitable for admin workflows
  and reindexing. In a production deployment, this could be replaced by a
  database or object store with versioning and ACLs.
"""
from __future__ import annotations
from pathlib import Path
import json
from typing import Dict, Any, List
import tempfile


class DocumentStore:
    def __init__(self, base_dir: str | Path):
        self.base = Path(base_dir) / "rag_documents"
        self.base.mkdir(parents=True, exist_ok=True)

    def _path_for(self, doc_id: str) -> Path:
        safe = doc_id.replace("/", "_")
        return self.base / f"{safe}.json"

    def save_doc(self, doc: Dict[str, Any]) -> None:
        p = self._path_for(doc["doc_id"])
        # if an existing doc is present, archive it as a version
        if p.exists():
            existing = json.loads(p.read_text(encoding="utf-8"))
            version = existing.get("version") or "v1"
            verdir = self.base / "versions" / doc["doc_id"]
            verdir.mkdir(parents=True, exist_ok=True)
            # version filename includes timestamp for uniqueness
            verpath = verdir / f"{version}_{int(Path(p).stat().st_mtime)}.json"
            verpath.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        # atomic write
        with tempfile.NamedTemporaryFile("w", delete=False, dir=str(self.base)) as tf:
            json.dump(doc, tf, ensure_ascii=False, indent=2)
            tmp_name = tf.name
        Path(tmp_name).replace(p)

    def load_doc(self, doc_id: str) -> Dict[str, Any] | None:
        p = self._path_for(doc_id)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def list_versions(self, doc_id: str) -> List[Dict[str, Any]]:
        verdir = self.base / "versions" / doc_id
        if not verdir.exists():
            return []
        versions = []
        for f in sorted(verdir.glob("*.json")):
            try:
                versions.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                continue
        return versions

    def revert_to_version(self, doc_id: str, timestamped_name: str) -> bool:
        verdir = self.base / "versions" / doc_id
        src = verdir / timestamped_name
        if not src.exists():
            return False
        current_path = self._path_for(doc_id)
        # archive current into versions as well
        if current_path.exists():
            existing = json.loads(current_path.read_text(encoding="utf-8"))
            verdir.mkdir(parents=True, exist_ok=True)
            verpath = verdir / f"revert_{int(Path(current_path).stat().st_mtime)}.json"
            verpath.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        # copy selected version to current
        current_path.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return True

    def list_docs(self) -> List[Dict[str, Any]]:
        docs = []
        for f in self.base.glob("*.json"):
            try:
                docs.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:
                # skip corrupt files but continue; log in real app
                continue
        return docs

    def delete_doc(self, doc_id: str) -> bool:
        p = self._path_for(doc_id)
        if p.exists():
            p.unlink()
            return True
        return False
