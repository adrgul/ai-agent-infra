import { useEffect, useState } from "react";
import { DebugInfo } from "../types";
import { fetchDebugInfo, deleteUserConversations } from "../api";
import "./DebugModal.css";

interface DebugModalProps {
  userId: number;
  isOpen: boolean;
  onClose: () => void;
  onConversationsDeleted?: () => void;
}

export function DebugModal({ userId, isOpen, onClose, onConversationsDeleted }: DebugModalProps) {
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const loadDebugInfo = () => {
    if (userId) {
      setIsLoading(true);
      setError(null);
      fetchDebugInfo(userId)
        .then(setDebugInfo)
        .catch((err) => {
          console.error("Failed to load debug info:", err);
          setError(err.message || "Failed to load debug information");
        })
        .finally(() => setIsLoading(false));
    }
  };

  useEffect(() => {
    if (isOpen && userId) {
      loadDebugInfo();
    }
  }, [isOpen, userId]);

  const handleDeleteConversations = async () => {
    if (!debugInfo) return;

    const confirmed = window.confirm(
      `Biztosan törölni akarod az összes beszélgetési előzményt (${debugInfo.user_data.firstname} ${debugInfo.user_data.lastname}) felhasználó számára?\n\nEz a művelet nem vonható vissza!`
    );

    if (!confirmed) return;

    setIsDeleting(true);
    setError(null);

    try {
      await deleteUserConversations(userId);
      // Refresh debug info after deletion
      loadDebugInfo();
      // Clear messages in chat window
      if (onConversationsDeleted) {
        onConversationsDeleted();
      }
    } catch (err: any) {
      console.error("Failed to delete conversations:", err);
      setError(err.message || "Failed to delete conversation history");
    } finally {
      setIsDeleting(false);
    }
  };

  if (!isOpen) return null;

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString("hu-HU");
  };

  return (
    <div className="debug-modal-overlay" onClick={onClose}>
      <div className="debug-modal" onClick={(e) => e.stopPropagation()}>
        <div className="debug-modal-header">
          <h2>Debug Information</h2>
          <button className="debug-modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="debug-modal-content">
          {isLoading && <div className="debug-loading">Loading...</div>}
          
          {error && <div className="debug-error">{error}</div>}
          
          {debugInfo && (
            <>
              {/* User Data Section */}
              <section className="debug-section">
                <h3>📊 Felhasználói adatok (adatbázis)</h3>
                <div className="debug-data-grid">
                  <div><strong>User ID:</strong> {debugInfo.user_data.user_id}</div>
                  <div><strong>Név:</strong> {debugInfo.user_data.firstname} {debugInfo.user_data.lastname}</div>
                  <div><strong>Becenév:</strong> {debugInfo.user_data.nickname}</div>
                  <div><strong>Email:</strong> {debugInfo.user_data.email}</div>
                  <div><strong>Role:</strong> {debugInfo.user_data.role}</div>
                  <div><strong>Nyelv:</strong> {debugInfo.user_data.default_lang || 'N/A'}</div>
                  <div><strong>Aktív:</strong> {debugInfo.user_data.is_active ? "Igen" : "Nem"}</div>
                  <div><strong>Létrehozva:</strong> {formatTimestamp(debugInfo.user_data.created_at)}</div>
                </div>
              </section>

              {/* AI Summary Section */}
              <section className="debug-section">
                <h3>🤖 AI Összefoglaló (LLM által generált)</h3>
                <div className="debug-summary">
                  {debugInfo.ai_summary}
                </div>
              </section>

              {/* Message Exchanges Section */}
              <section className="debug-section">
                <div className="debug-section-header">
                  <h3>💬 Utolsó 10 üzenetváltás</h3>
                  {debugInfo.last_exchanges.length > 0 && (
                    <button
                      className="delete-history-button"
                      onClick={handleDeleteConversations}
                      disabled={isDeleting}
                    >
                      🗑️ {isDeleting ? "Törlés..." : "Előzmények törlése"}
                    </button>
                  )}
                </div>
                {debugInfo.last_exchanges.length === 0 ? (
                  <div className="debug-no-data">Nincs még üzenetváltás</div>
                ) : (
                  <div className="debug-exchanges">
                    {debugInfo.last_exchanges.map((exchange, index) => (
                      <div key={index} className="debug-exchange">
                        <div className="debug-exchange-header">
                          <strong>#{debugInfo.last_exchanges.length - index}</strong>
                          <span className="debug-timestamp">
                            {formatTimestamp(exchange.timestamp)}
                          </span>
                        </div>
                        <div className="debug-message debug-user-message">
                          <strong>👤 User:</strong>
                          <div>{exchange.user_message}</div>
                        </div>
                        {exchange.assistant_message && (
                          <div className="debug-message debug-assistant-message">
                            <strong>🤖 Assistant:</strong>
                            <div>{exchange.assistant_message}</div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
