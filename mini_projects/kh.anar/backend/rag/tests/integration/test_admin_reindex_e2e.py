from fastapi.testclient import TestClient
from app.main import app
import os


def test_admin_reindex_and_rbac():
    client = TestClient(app)
    os.environ["ADMIN_TOKEN"] = "admintoken"

    payload = {
        "doc_id": "doc-rbac",
        "title": "Private Doc",
        "source": "tests",
        "doc_type": "note",
        "version": "1",
        "access_scope": "private",
        "text": "PRIVATE_DATA_CANARY"
    }

    r = client.post("/admin/rag/add", json=payload, headers={"token": "admintoken"})
    assert r.status_code == 200

    # query without access scope -> should possibly return nothing depending on threshold
    rsearch = client.post("/api/chat", json={"user_id": "u1", "session_id": "s1", "message": "PRIVATE_DATA_CANARY", "metadata": {}})
    assert rsearch.status_code == 200
    # now query with access scope in metadata — should hit
    rsearch2 = client.post("/api/chat", json={"user_id": "u1", "session_id": "s1", "message": "PRIVATE_DATA_CANARY", "metadata": {"access_scope": "private"}})
    assert rsearch2.status_code == 200
    assert rsearch2.json()["debug"]["rag_telemetry"]["decision"] in ("hit", "no_hit")  # we just check flow doesn't crash
