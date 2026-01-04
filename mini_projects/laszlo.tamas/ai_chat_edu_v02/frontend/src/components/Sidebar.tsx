import { useState, useEffect, ChangeEvent, KeyboardEvent, MouseEvent, useCallback, useImperativeHandle, forwardRef } from "react";
import "./Sidebar.css";

export interface SessionInfo {
  id: string;
  title: string;
  created_at: string;
  last_message_at: string;
  is_deleted: boolean;
  processed_for_ltm: boolean;
  message_count: number;
}

export interface SidebarRef {
  refreshSessions: () => Promise<void>;
}

interface SidebarProps {
  userId: number;
  activeSessionId: string | null;
  onSessionSelect: (sessionId: string) => void;
  onNewChat: () => void;
  onSessionDelete: (sessionId: string) => void;
  onSessionRename: (sessionId: string, newTitle: string) => void;
}

interface GroupedSessions {
  today: SessionInfo[];
  yesterday: SessionInfo[];
  last7Days: SessionInfo[];
  last30Days: SessionInfo[];
  older: SessionInfo[];
}

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:18000/api";

export const Sidebar = forwardRef<SidebarRef, SidebarProps>(function Sidebar({
  userId,
  activeSessionId,
  onSessionSelect,
  onNewChat,
  onSessionDelete,
  onSessionRename
}, ref) {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const SESSION_LIMIT = 10;

  const fetchSessions = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/sessions?user_id=${userId}`);
      const data = await response.json();
      // Sort by last_message_at descending
      const sorted = (data.sessions || []).sort((a: SessionInfo, b: SessionInfo) => 
        new Date(b.last_message_at).getTime() - new Date(a.last_message_at).getTime()
      );
      setSessions(sorted);
    } catch (error) {
      console.error("Failed to fetch sessions:", error);
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  // Expose refresh method to parent via ref
  useImperativeHandle(ref, () => ({
    refreshSessions: fetchSessions
  }), [fetchSessions]);

  // Fetch sessions when userId changes
  useEffect(() => {
    if (userId) {
      fetchSessions();
    }
  }, [userId, fetchSessions]);

  const handleDeleteSession = async (sessionId: string, e: MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Biztosan törölni szeretnéd ezt a beszélgetést?")) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: "DELETE"
      });
      if (response.ok) {
        setSessions((prev: SessionInfo[]) => prev.filter((s: SessionInfo) => s.id !== sessionId));
        onSessionDelete(sessionId);
      }
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  };

  const handleStartEdit = (session: SessionInfo, e: MouseEvent) => {
    e.stopPropagation();
    setEditingSessionId(session.id);
    setEditingTitle(session.title || "Új beszélgetés");
  };

  const handleSaveEdit = async (sessionId: string) => {
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/title`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: editingTitle.trim() })
      });

      if (response.ok) {
        setSessions((prev: SessionInfo[]) =>
          prev.map((s: SessionInfo) => s.id === sessionId ? { ...s, title: editingTitle.trim() } : s)
        );
        onSessionRename(sessionId, editingTitle.trim());
      }
    } catch (error) {
      console.error("Failed to rename session:", error);
    } finally {
      setEditingSessionId(null);
    }
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditingTitle("");
  };

  // Group sessions by date
  const groupSessionsByDate = (sessions: SessionInfo[]): GroupedSessions => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const last7Days = new Date(today);
    last7Days.setDate(last7Days.getDate() - 7);
    const last30Days = new Date(today);
    last30Days.setDate(last30Days.getDate() - 30);

    const grouped: GroupedSessions = {
      today: [],
      yesterday: [],
      last7Days: [],
      last30Days: [],
      older: []
    };

    sessions.forEach(session => {
      const sessionDate = new Date(session.last_message_at);
      if (sessionDate >= today) {
        grouped.today.push(session);
      } else if (sessionDate >= yesterday) {
        grouped.yesterday.push(session);
      } else if (sessionDate >= last7Days) {
        grouped.last7Days.push(session);
      } else if (sessionDate >= last30Days) {
        grouped.last30Days.push(session);
      } else {
        grouped.older.push(session);
      }
    });

    return grouped;
  };

  const groupedSessions = groupSessionsByDate(sessions);

  const renderSessionItem = (session: SessionInfo) => {
    const isActive = session.id === activeSessionId;
    const isEditing = session.id === editingSessionId;

    // Format date-time
    const formatDateTime = (dateStr: string) => {
      const date = new Date(dateStr);
      const now = new Date();
      const isToday = date.toDateString() === now.toDateString();
      
      if (isToday) {
        // Today: show only time (HH:MM)
        return date.toLocaleTimeString('hu-HU', { hour: '2-digit', minute: '2-digit' });
      } else {
        // Other days: show date + time (MM.DD HH:MM)
        return date.toLocaleString('hu-HU', { 
          month: '2-digit', 
          day: '2-digit', 
          hour: '2-digit', 
          minute: '2-digit' 
        });
      }
    };

    return (
      <div
        key={session.id}
        className={`session-item ${isActive ? "active" : ""}`}
        onClick={() => !isEditing && onSessionSelect(session.id)}
      >
        {isEditing ? (
          <input
            type="text"
            className="session-title-input"
            value={editingTitle}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEditingTitle(e.target.value)}
            onBlur={() => handleSaveEdit(session.id)}
            onKeyDown={(e: KeyboardEvent<HTMLInputElement>) => {
              if (e.key === "Enter") handleSaveEdit(session.id);
              if (e.key === "Escape") handleCancelEdit();
            }}
            autoFocus
            onClick={(e: MouseEvent<HTMLInputElement>) => e.stopPropagation()}
          />
        ) : (
          <>
            <div className="session-info">
              <div className="session-title">{session.title || "Új beszélgetés"}</div>
              <div className="session-time">{formatDateTime(session.last_message_at)}</div>
            </div>
            <div className="session-actions">
              <button
                className="session-action-btn"
                onClick={(e: MouseEvent<HTMLButtonElement>) => handleStartEdit(session, e)}
                title="Átnevezés"
              >
                ✏️
              </button>
              <button
                className="session-action-btn"
                onClick={(e: MouseEvent<HTMLButtonElement>) => handleDeleteSession(session.id, e)}
                title="Törlés"
              >
                🗑️
              </button>
            </div>
          </>
        )}
      </div>
    );
  };

  const renderSessionGroup = (title: string, sessions: SessionInfo[]) => {
    if (sessions.length === 0) return null;

    return (
      <div className="session-group">
        <div className="session-group-title">{title}</div>
        {sessions.map(renderSessionItem)}
      </div>
    );
  };

  if (isCollapsed) {
    return (
      <div className="sidebar collapsed">
        <button className="collapse-toggle" onClick={() => setIsCollapsed(false)}>
          ▶
        </button>
      </div>
    );
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewChat}>
          🆕 Új beszélgetés
        </button>
        <button className="collapse-toggle" onClick={() => setIsCollapsed(true)}>
          ◀
        </button>
      </div>

      <div className="session-list">
        {isLoading ? (
          <div className="session-loading">Betöltés...</div>
        ) : sessions.length === 0 ? (
          <div className="session-empty">Nincs még beszélgetés</div>
        ) : (
          <>
            {renderSessionGroup("📅 Ma", groupedSessions.today.slice(0, showAll ? undefined : SESSION_LIMIT))}
            {renderSessionGroup("📅 Tegnap", groupedSessions.yesterday.slice(0, showAll ? undefined : SESSION_LIMIT))}
            {renderSessionGroup("📅 Elmúlt 7 nap", groupedSessions.last7Days.slice(0, showAll ? undefined : SESSION_LIMIT))}
            {renderSessionGroup("📅 Elmúlt 30 nap", groupedSessions.last30Days.slice(0, showAll ? undefined : SESSION_LIMIT))}
            {renderSessionGroup("📅 Régebbi", groupedSessions.older.slice(0, showAll ? undefined : SESSION_LIMIT))}
            
            {!showAll && sessions.length > SESSION_LIMIT && (
              <button className="load-more-btn" onClick={() => setShowAll(true)}>
                További beszélgetések ({sessions.length - SESSION_LIMIT})
              </button>
            )}
          </>
        )}
      </div>
    </div>
  );
});
