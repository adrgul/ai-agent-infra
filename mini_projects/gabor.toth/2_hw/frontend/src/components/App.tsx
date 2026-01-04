import React, { useState, useEffect } from 'react';
import '../styles/app.css';
import { UploadPanel } from './UploadPanel';
import { Chat } from './Chat';
import ActivityLogger from './ActivityLogger';
import { categoriesAPI } from '../api';
import { ActivityProvider } from '../contexts/ActivityContext';

export const App: React.FC = () => {
  const [sessionId] = useState(() => {
    let id = localStorage.getItem('sessionId');
    if (!id) {
      id = `session_${Date.now()}`;
      localStorage.setItem('sessionId', id);
    }
    return id;
  });

  const [categories, setCategories] = useState<string[]>([]);
  const [error, setError] = useState<string>('');
  const [debugInfo, setDebugInfo] = useState<any>(null);
  const [systemUsername, setSystemUsername] = useState<string>('');

  useEffect(() => {
    loadCategories();
    loadSystemInfo();
  }, []);

  const loadSystemInfo = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/system-info');
      if (response.ok) {
        const data = await response.json();
        setSystemUsername(data.username);
      }
    } catch (err) {
      console.error('Error loading system info:', err);
      setSystemUsername('unknown');
    }
  };

  const loadCategories = async () => {
    try {
      const cats = await categoriesAPI.getCategories();
      console.log('Categories loaded from API:', cats);
      setCategories(cats);
      setError('');
    } catch (err: any) {
      console.error('Error loading categories:', err);
      setCategories([]);
      setError('Kategóriák betöltési hiba');
    }
  };

  const handleUploadSuccess = () => {
    loadCategories();
  };

  const handleError = (msg: string) => {
    setError(msg);
    setTimeout(() => setError(''), 5000);
  };

  const handleDeleteCategory = async (category: string) => {
    const confirmed = window.confirm(`Valóban törölni szeretnéd a "${category}" kategóriát és összes dokumentumát?`);
    if (!confirmed) return;

    try {
      await categoriesAPI.deleteCategory(category);
      setError('');
      loadCategories();
      alert(`"${category}" kategória sikeresen törölve.`);
    } catch (err: any) {
      console.error('Delete category error:', err);
      setError('Kategória törlési hiba: ' + (err.message || String(err)));
    }
  };

  const handleShutdown = async () => {
    const confirmed = window.confirm('Valóban leállítod a szervert?');
    if (!confirmed) return;

    try {
      const response = await fetch('http://localhost:8000/api/shutdown', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });

      if (response.ok) {
        alert('🛑 Szerver leállítása indult...\n\nA backend leállítása folyamatban van.');
        // NEM zárjuk be az ablakot - hagyjuk futni az oldalt
        // A böngésző megpróbál majd csatlakozni, ha újra online lesz
      } else {
        setError('Shutdown nem sikerült');
      }
    } catch (err) {
      console.error('Shutdown error:', err);
      setError('Shutdown hiba: ' + String(err));
    }
  };

  return (
    <ActivityProvider>
      <div className="app">
        <header className="app-header">
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <button className="shutdown-btn" onClick={handleShutdown} title="Szerver leállítása">
              🛑 Kilépés
            </button>
            <div className="user-info">user: {systemUsername}</div>
          </div>
          <h1>RAG Agent - Dokumentum szintű AI Asszisztens</h1>
          <div style={{ display: 'flex', gap: '10px' }}>
            <ActivityLogger />
          </div>
        </header>

        <div className="app-container">
          <aside className="sidebar">
            <UploadPanel
              userId={systemUsername}
              categories={categories}
              onUploadSuccess={handleUploadSuccess}
              onError={handleError}
              onDeleteCategory={handleDeleteCategory}
            />

            {debugInfo && (
              <div className="debug-panel">
                <h3>Debug Infó</h3>
                <p>Routed category: {debugInfo.routed_category || 'none'}</p>
                {debugInfo.retrieved?.length > 0 && (
                  <div className="retrieved-chunks">
                    <p>Retrieved chunks: {debugInfo.retrieved.length}</p>
                    {debugInfo.retrieved.map((chunk: any, idx: number) => (
                      <div key={idx} className="chunk-preview">
                        <strong>{chunk.chunk_id}</strong>
                        <p>{chunk.snippet}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </aside>

          <main className="main-content">
            <Chat userId={systemUsername} sessionId={sessionId} onDebugInfo={setDebugInfo} />
          </main>
        </div>

        {error && <div className="error-notification">{error}</div>}
      </div>
    </ActivityProvider>
  );
};
