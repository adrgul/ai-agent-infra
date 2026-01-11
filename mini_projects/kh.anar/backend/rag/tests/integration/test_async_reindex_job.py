import time
from fastapi.testclient import TestClient
from app.main import app
import os


def test_start_async_reindex_and_poll(monkeypatch):
    client = TestClient(app)
    os.environ["ADMIN_TOKEN"] = "async-token"

    # add a doc first
    payload = {
        "doc_id": "doc-async",
        "title": "Async Doc",
        "source": "tests",
        "doc_type": "note",
        "version": "1",
        "access_scope": "public",
        "text": "ASYNC_CANARY"
    }
    r = client.post("/admin/rag/add", json=payload, headers={"token": "async-token"})
    assert r.status_code == 200

    r2 = client.post("/admin/rag/reindex_async", headers={"token": "async-token"})
    assert r2.status_code == 200
    job_id = r2.json().get("job_id")
    assert job_id

    status = None
    timeout = time.time() + 10
    while time.time() < timeout:
        s = client.get(f"/admin/rag/reindex_status/{job_id}", headers={"token": "async-token"})
        assert s.status_code == 200
        info = s.json()["info"]
        status = info.get("status")
        if status in ("finished", "failed"):
            break
        time.sleep(0.2)

    assert status == "finished"
    result = s.json()["info"]["result"]
    assert result and result.get("reindexed_chunks", 0) > 0
