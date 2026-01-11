import os
import tempfile
import pytest

try:
    import chromadb
    from chromadb.config import Settings
except Exception:
    chromadb = None


@pytest.mark.skipif(chromadb is None, reason="chromadb not installed")
def test_chroma_persistence_roundtrip():
    tmp = tempfile.TemporaryDirectory()
    settings = Settings(chroma_db_impl="duckdb+parquet", persist_directory=tmp.name)
    client = chromadb.Client(settings=settings)
    col = client.create_collection(name="test_persist")
    col.add(ids=["a"], documents=["hello world"], metadatas=[{"doc_id": "doc1"}], embeddings=[[0.1] * 32])
    # close and re-open client
    client = chromadb.Client(settings=settings)
    col2 = client.get_or_create_collection(name="test_persist")
    res = col2.query(query_embeddings=[[0.1] * 32], n_results=1)
    assert res["ids"][0][0] == "a"
    tmp.cleanup()
