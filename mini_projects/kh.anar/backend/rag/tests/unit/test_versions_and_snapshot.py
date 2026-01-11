import tempfile
from pathlib import Path
from rag.persistence.store import DocumentStore


def test_versions_and_snapshot(tmp_path):
    ds = DocumentStore(base_dir=tmp_path)
    doc_v1 = {"doc_id": "vdoc", "version": "v1", "title": "T1", "text": "hello"}
    ds.save_doc(doc_v1)
    doc_v2 = {"doc_id": "vdoc", "version": "v2", "title": "T2", "text": "hello2"}
    ds.save_doc(doc_v2)

    versions = ds.list_versions("vdoc")
    assert versions
    # snapshot: create tar.gz
    snap_name = tmp_path / "snapshot_test.tar.gz"
    import tarfile
    with tarfile.open(snap_name, "w:gz") as tf:
        tf.add(ds.base, arcname=ds.base.name)
    assert snap_name.exists()

    # revert to first version (find the filename)
    verdir = tmp_path / "rag_documents" / "versions" / "vdoc"
    files = sorted([f.name for f in verdir.glob("*.json")])
    assert files
    ok = ds.revert_to_version("vdoc", files[0])
    assert ok
    loaded = ds.load_doc("vdoc")
    assert loaded
