import React, { useState } from 'react';
import { Upload, AlertCircle } from 'lucide-react';

import MeetingList from './components/MeetingList';
import SummarySection from './components/SummarySection';
import NotesSection from './components/NotesSection';
import TasksSection from './components/TasksSection';

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handlUpload = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        if (response.status === 409) {
          throw new Error("This file has already been processed.");
        }
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <div className="header-brand">
          <h1>MeetingAI</h1>
          <p>Automated Meeting Summarizer</p>
        </div>
        <nav className="header-nav">
          <ul className="nav-menu">
            <li>
              <a
                href="#"
                className={`nav-link ${activeTab === 'upload' ? 'active' : ''}`}
                onClick={(e) => { e.preventDefault(); setActiveTab('upload'); }}
              >
                Upload & Generate
              </a>
            </li>
            <li>
              <a
                href="#"
                className={`nav-link ${activeTab === 'saved' ? 'active' : ''}`}
                onClick={(e) => { e.preventDefault(); setActiveTab('saved'); }}
              >
                Saved Meetings
              </a>
            </li>
          </ul>
        </nav>
      </header>

      <main className="main-content">
        {activeTab === 'upload' ? (
          <>
            <section className="upload-section card">
              <div className="upload-area">
                <Upload size={48} className="icon-primary" />
                <h2>Upload Transcript</h2>
                <p>Select a .txt, .md, .srt, or .docx file to process</p>
                <input
                  type="file"
                  accept=".txt,.md,.srt,.docx"
                  onChange={handleFileChange}
                  id="file-upload"
                  className="file-input"
                />
                <label htmlFor="file-upload" className="file-label">
                  {file ? file.name : "Choose File"}
                </label>
                <button
                  className="btn-primary"
                  onClick={handlUpload}
                  disabled={!file || loading}
                >
                  {loading ? "Processing..." : "Process Transcript"}
                </button>
              </div>
              {error && <div className="error-message"><AlertCircle size={16} /> {error}</div>}
            </section>

            {result && (
              <div className="results-grid">
                <SummarySection summary={result.summary} />
                <NotesSection notes={result.notes} />
                <TasksSection tasks={result.tasks} />
              </div>
            )}
          </>
        ) : (
          <MeetingList />
        )}
      </main>
    </div>
  );
}

export default App;
