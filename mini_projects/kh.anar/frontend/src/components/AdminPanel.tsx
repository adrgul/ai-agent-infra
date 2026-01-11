import React, { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const ADMIN_BASE = API_BASE.replace("/api", "/admin");

const AdminPanel: React.FC = () => {
  const [status, setStatus] = useState("");

  const addDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    const form = e.target as any;
    const payload = {
      doc_id: form.doc_id.value,
      title: form.title.value,
      source: form.source.value,
      doc_type: form.doc_type.value,
      version: form.version.value,
      access_scope: form.access_scope.value,
      text: form.text.value,
    };
    const token = (window as any).ADMIN_TOKEN || "changeme";
    const res = await fetch(`${ADMIN_BASE}/rag/add`, { method: "POST", headers: { "Content-Type": "application/json", token }, body: JSON.stringify(payload) });
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  const reindex = async () => {
    const token = (window as any).ADMIN_TOKEN || "changeme";
    const res = await fetch(`${ADMIN_BASE}/rag/reindex`, { method: "POST", headers: { token } });
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  const deleteDoc = async (id: string) => {
    const token = (window as any).ADMIN_TOKEN || "changeme";
    const res = await fetch(`${ADMIN_BASE}/rag/doc/${id}`, { method: "DELETE", headers: { token } });
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  const listVersions = async (id: string) => {
    const token = (window as any).ADMIN_TOKEN || "changeme";
    const res = await fetch(`${ADMIN_BASE}/rag/doc/${id}/versions`, { method: "GET", headers: { token } });
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  const revert = async (id: string, ver: string) => {
    const token = (window as any).ADMIN_TOKEN || "changeme";
    const res = await fetch(`${ADMIN_BASE}/rag/doc/${id}/revert?version_name=${encodeURIComponent(ver)}`, { method: "POST", headers: { token } });
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  const snapshot = async () => {
    const token = (window as any).ADMIN_TOKEN || "changeme";
    const res = await fetch(`${ADMIN_BASE}/rag/snapshot`, { method: "POST", headers: { token } });
    const data = await res.json();
    setStatus(JSON.stringify(data));
  };

  return (
    <div className="admin-panel">
      <h4>Admin</h4>
      <form onSubmit={addDoc}>
        <input name="doc_id" placeholder="doc id" />
        <input name="title" placeholder="title" />
        <input name="source" placeholder="source" />
        <input name="doc_type" placeholder="doc type" />
        <input name="version" placeholder="version" />
        <input name="access_scope" placeholder="access scope" />
        <textarea name="text" placeholder="text" />
        <button type="submit">Add / Update</button>
      </form>
      <div className="uk-margin-small-top">
        <button onClick={reindex}>Reindex All</button>
        <button onClick={() => deleteDoc((document.getElementsByName("doc_id")[0] as HTMLInputElement).value)}>Delete</button>
        <button onClick={() => listVersions((document.getElementsByName("doc_id")[0] as HTMLInputElement).value)}>List Versions</button>
        <button onClick={() => snapshot()}>Snapshot</button>
      </div>
      <pre>{status}</pre>
    </div>
  );
};

export default AdminPanel;
