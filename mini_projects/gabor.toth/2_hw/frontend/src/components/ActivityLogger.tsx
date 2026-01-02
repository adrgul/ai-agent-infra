import React, { useEffect, useRef, useState } from 'react';
import { useActivity, LogEntry } from '../contexts/ActivityContext';
import '../styles/activity-logger.css';

const ActivityLogger: React.FC = () => {
  const { entries, clearActivities, addActivity } = useActivity();
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [apiActivities, setApiActivities] = useState<any[]>([]);
  const contentRef = useRef<HTMLDivElement>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch activities from backend API
  const fetchActivities = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/activities?count=100');
      if (response.ok) {
        const data = await response.json();
        setApiActivities(data.activities || []);
      }
    } catch (error) {
      console.error('Failed to fetch activities:', error);
    }
  };

  // Start polling when panel is open
  useEffect(() => {
    if (isOpen) {
      fetchActivities(); // Fetch immediately
      pollingIntervalRef.current = setInterval(fetchActivities, 1000); // Poll every 1 second
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [isOpen]);

  const formatTime = (timestamp: any): string => {
    try {
      if (!timestamp) return 'Ismeretlen idő';
      
      let date: Date;
      
      // Ha szám, direkten milliszekundumként kezelj
      if (typeof timestamp === 'number') {
        date = new Date(timestamp);
      } 
      // Ha string (ISO format), parseld
      else if (typeof timestamp === 'string') {
        date = new Date(timestamp);
      }
      // Egyéb esetben skip
      else {
        return 'Érvénytelen formátum';
      }
      
      // Ellenőrizd, hogy valid dátum-e
      if (isNaN(date.getTime())) {
        console.error('Invalid timestamp:', timestamp);
        return 'Érvénytelen dátum';
      }
      
      return date.toLocaleTimeString('hu-HU', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (e) {
      console.error('Date formatting error:', e, 'timestamp:', timestamp);
      return 'Dátumhiba';
    }
  };

  const getTypeIcon = (type: string): string => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✗';
      case 'warning':
        return '⚠';
      case 'processing':
        return '⏳';
      case 'info':
      default:
        return 'ℹ';
    }
  };

  // Combine local entries with API activities and sort by timestamp
  const allActivities = [...apiActivities, ...entries].sort((a, b) => {
    const timeA = new Date(a.timestamp).getTime();
    const timeB = new Date(b.timestamp).getTime();
    return timeB - timeA; // Newest first
  });

  return (
    <div className="activity-logger">
      <button
        className="activity-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        title={isOpen ? 'Bezárás' : 'Megnyitás'}
      >
        📋 Tevékenység ({allActivities.length})
      </button>

      {isOpen && (
        <>
          <div className="activity-overlay" onClick={() => setIsOpen(false)}></div>
          <div className={`activity-panel ${isExpanded ? 'expanded' : ''}`}>
            <div className="activity-panel-header">
              <h3>📋 Háttérfolyamatok</h3>
              <div className="activity-panel-controls">
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  title={isExpanded ? 'Kis méret' : 'Teljes méret'}
                  className="expand-btn"
                >
                  {isExpanded ? '🔽' : '🔼'}
                </button>
                <button 
                  onClick={() => {
                    clearActivities();
                    setApiActivities([]);
                  }} 
                  title="Törlés"
                >
                  🗑
                </button>
                <button onClick={() => setIsOpen(false)} title="Bezárás" className="close-btn">
                  ✕
                </button>
              </div>
            </div>

            <div className="activity-panel-content" ref={contentRef}>
              {allActivities.length === 0 ? (
                <div className="empty-state">
                  <p>Nincsenek folyamatok...</p>
                </div>
              ) : (
                <ul className="activity-list">
                  {allActivities.map(entry => (
                    <li
                      key={entry.id}
                      className={`activity-item activity-${entry.type}`}
                    >
                      <div className="activity-icon">{getTypeIcon(entry.type)}</div>
                      <div className="activity-content">
                        <div className="activity-message">{entry.message}</div>
                        <div className="activity-time">
                          {formatTime(entry.timestamp)}
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="activity-panel-footer">
              Összesen: {allActivities.length} esemény
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ActivityLogger;

