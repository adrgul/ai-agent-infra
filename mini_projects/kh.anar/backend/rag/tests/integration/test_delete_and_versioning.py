from fastapi.testclient import TestClient
from app.main import app
import os
from pathlib import Path


def test_delete_and_versions_flow(tmp_path):
    client = TestClient(app)
    os.environ["ADMIN_TOKEN"] = "vtok"

    payload = {
        "doc_id": "vdoc",
        "title": "VDoc",
        "source": "tests",
        "doc_type": "note",
        "version": "v1",
        "access_scope": "public",
        "text": "VER_1"
    }
    r = client.post("/admin/rag/add", json=payload, headers={"token": "vtok"})
    assert r.status_code == 200

    payload2 = {**payload, "version": "v2", "text": "VER_2"}
    r2 = client.post("/admin/rag/add", json=payload2, headers={"token": "vtok"})
    assert r2.status_code == 200

    vs = client.get("/admin/rag/doc/vdoc/versions", headers={"token": "vtok"})
    assert vs.status_code == 200
    versions = vs.json().get("versions")
    assert versions and len(versions) >= 1

    # revert to first version
    ver_name = versions[0]["name"]
    rv = client.post(f"/admin/rag/doc/vdoc/revert?version_name={ver_name}", headers={"token": "vtok"})
    assert rv.status_code == 200

    # delete
    d = client.delete("/admin/rag/doc/vdoc", headers={"token": "vtok"})
    assert d.status_code == 200
    # ensure file removed
    assert not (Path('.') / 'rag_documents' / 'vdoc.json').exists()
