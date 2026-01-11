import tempfile
from rag.persistence.store import DocumentStore


def test_store_save_load_list_delete(tmp_path):
    ds = DocumentStore(base_dir=tmp_path)
    doc = {"doc_id": "d1", "title": "T1", "text": "hello"}

    ds.save_doc(doc)
    loaded = ds.load_doc("d1")
    assert loaded is not None
    assert loaded["title"] == "T1"

    docs = ds.list_docs()
    assert any(d["doc_id"] == "d1" for d in docs)

    ok = ds.delete_doc("d1")
    assert ok
    assert ds.load_doc("d1") is None
