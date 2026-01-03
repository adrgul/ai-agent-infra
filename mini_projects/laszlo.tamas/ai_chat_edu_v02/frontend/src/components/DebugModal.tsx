import { useEffect, useState } from "react";
import { DebugInfo } from "../types";
import { fetchDebugInfo, deleteUserConversations, resetPostgres, resetQdrant, resetCache } from "../api";
import { useWorkflowState } from "../hooks/useWorkflowState";
import { WorkflowStateInspector } from "./WorkflowStateInspector";
import { CacheDebugSection } from "./CacheDebugSection";
import "./DebugModal.css";

interface DebugModalProps {
  userId: number;
  sessionId: string | null;
  isOpen: boolean;
  onClose: () => void;
  onConversationsDeleted?: () => void;
}

export function DebugModal({ userId, sessionId, isOpen, onClose, onConversationsDeleted }: DebugModalProps) {
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isResettingPostgres, setIsResettingPostgres] = useState(false);
  const [isResettingQdrant, setIsResettingQdrant] = useState(false);
  const [isResettingCache, setIsResettingCache] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  
  // Accordion states
  const [accordionOpen, setAccordionOpen] = useState({
    userData: true,
    workflowState: false,
    messageHistory: false,
    cacheStats: false,
    resetActions: false
  });
  
  // Workflow state WebSocket (only enabled when accordion is open)
  const {
    stateHistory,
    latestState,
    currentNode,
    isConnected,
    clearHistory
  } = useWorkflowState({
    enabled: isOpen && accordionOpen.workflowState,
    sessionId: sessionId
  });

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

  // Initial load when modal opens
  useEffect(() => {
    if (isOpen && userId) {
      loadDebugInfo();
      // Clear workflow history when modal opens
      clearHistory();
    }
  }, [isOpen, userId]);
  
  const toggleAccordion = (section: keyof typeof accordionOpen) => {
    setAccordionOpen(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };
  
  const handleResetCache = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to clear ALL caches?\n\nThis will clear:\n- Database cache (cached_prompts table)\n- Python memory cache\n\nThis action cannot be undone!"
    );

    if (!confirmed) return;

    setIsResettingCache(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await resetCache();
      setSuccessMessage(`Cache cleared! DB rows: ${result.db_cleared}, Memory: ${result.memory_cleared ? 'Cleared' : 'Failed'}`);
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err: any) {
      console.error("Failed to reset cache:", err);
      setError(err.message || "Failed to reset cache");
    } finally {
      setIsResettingCache(false);
    }
  };

  const handleResetPostgres = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete ALL documents and chunks from PostgreSQL?\n\nThis will remove all uploaded documents and their metadata.\n\nThis action cannot be undone!"
    );

    if (!confirmed) return;

    setIsResettingPostgres(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await resetPostgres();
      setSuccessMessage(`PostgreSQL reset successful! Deleted ${result.documents_deleted} documents and ${result.chunks_deleted} chunks.`);
      setTimeout(() => setSuccessMessage(null), 5000);
      loadDebugInfo();
    } catch (err: any) {
      console.error("Failed to reset PostgreSQL:", err);
      setError(err.message || "Failed to reset PostgreSQL");
    } finally {
      setIsResettingPostgres(false);
    }
  };

  const handleResetQdrant = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to delete ALL document vectors from Qdrant?\n\nThis will remove all document embeddings from the vector database.\n\nThis action cannot be undone!"
    );

    if (!confirmed) return;

    setIsResettingQdrant(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await resetQdrant();
      setSuccessMessage(`Qdrant reset successful! ${result.message}`);
      setTimeout(() => setSuccessMessage(null), 5000);
      loadDebugInfo();
    } catch (err: any) {
      console.error("Failed to reset Qdrant:", err);
      setError(err.message || "Failed to reset Qdrant");
    } finally {
      setIsResettingQdrant(false);
    }
  };

  const handleDeleteConversations = async () => {
    if (!debugInfo) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete all conversation history for user ${debugInfo.user_data.firstname} ${debugInfo.user_data.lastname}?\n\nThis action cannot be undone!`
    );

    if (!confirmed) return;

    setIsDeleting(true);
    setError(null);

    try {
      await deleteUserConversations(userId);
      setSuccessMessage("Chat history deleted successfully!");
      setTimeout(() => setSuccessMessage(null), 3000);
      loadDebugInfo();
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
    <div className="debug-panel">
      <div className="debug-panel-header">
        <h2>Debug Information</h2>
        <div className="debug-panel-controls">
          <button className="debug-panel-close" onClick={onClose}>
            ×
          </button>
        </div>
      </div>

      <div className="debug-panel-content">
          {isLoading && <div className="debug-loading">Loading...</div>}
          
          {error && <div className="debug-error">{error}</div>}
          {successMessage && <div className="debug-success">{successMessage}</div>}
          
          {debugInfo && (
            <>
              {/* ACCORDION 1: User Data */}
              <section className="debug-section">
                <div 
                  className="debug-accordion-header"
                  onClick={() => toggleAccordion('userData')}
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                >
                  <h3>
                    {accordionOpen.userData ? '▼' : '▶'} 📊 User Data (Database)
                  </h3>
                </div>
                {accordionOpen.userData && (
                  <div className="debug-data-grid" style={{ marginTop: '10px' }}>
                    <div><strong>User ID:</strong> {debugInfo.user_data.user_id}</div>
                    <div><strong>Name:</strong> {debugInfo.user_data.firstname} {debugInfo.user_data.lastname}</div>
                    <div><strong>Nickname:</strong> {debugInfo.user_data.nickname}</div>
                    <div><strong>Email:</strong> {debugInfo.user_data.email}</div>
                    <div><strong>Role:</strong> {debugInfo.user_data.role}</div>
                    <div><strong>Language:</strong> {debugInfo.user_data.default_lang || 'N/A'}</div>
                    <div><strong>Active:</strong> {debugInfo.user_data.is_active ? "Yes" : "No"}</div>
                    <div><strong>Created:</strong> {formatTimestamp(debugInfo.user_data.created_at)}</div>
                  </div>
                )}
              </section>

              {/* ACCORDION 2: Workflow State (WebSocket) */}
              <section className="debug-section">
                <div 
                  className="debug-accordion-header"
                  onClick={() => toggleAccordion('workflowState')}
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                >
                  <h3>
                    {accordionOpen.workflowState ? '▼' : '▶'} 🔄 Workflow State (Real-time)
                  </h3>
                </div>
                {accordionOpen.workflowState && (
                  <div style={{ marginTop: '10px' }}>
                    <WorkflowStateInspector
                      stateHistory={stateHistory}
                      latestState={latestState}
                      currentNode={currentNode}
                      isConnected={isConnected}
                    />
                  </div>
                )}
              </section>

              {/* ACCORDION 3: Message History */}
              <section className="debug-section">
                <div 
                  className="debug-accordion-header"
                  onClick={() => toggleAccordion('messageHistory')}
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                >
                  <h3>
                    {accordionOpen.messageHistory ? '▼' : '▶'} 💬 Last 10 Message Exchanges
                  </h3>
                </div>
                {accordionOpen.messageHistory && (
                  <div style={{ marginTop: '10px' }}>
                    <div className="debug-section-header">
                      <button
                        className="refresh-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          loadDebugInfo();
                        }}
                        disabled={isLoading}
                        title="Refresh message history"
                      >
                        🔄 {isLoading ? "Loading..." : "Refresh"}
                      </button>
                      {debugInfo.last_exchanges.length > 0 && (
                        <button
                          className="delete-history-button"
                          onClick={handleDeleteConversations}
                          disabled={isDeleting}
                        >
                          🗑️ {isDeleting ? "Deleting..." : "Clear History"}
                        </button>
                      )}
                    </div>
                    {debugInfo.last_exchanges.length === 0 ? (
                      <div className="debug-no-data">No message exchanges yet</div>
                    ) : (
                      <div className="debug-exchanges">
                        {[...debugInfo.last_exchanges].reverse().map((exchange, index) => (
                          <div key={index} className="debug-exchange">
                            <div className="debug-exchange-header">
                              <strong>#{index + 1}</strong>
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
                  </div>
                )}
              </section>

              {/* ACCORDION 4: Cache Statistics (P0.17) */}
              <CacheDebugSection />

              {/* ACCORDION 5: Reset Actions */}
              <section className="debug-section">
                <div 
                  className="debug-accordion-header"
                  onClick={() => toggleAccordion('resetActions')}
                  style={{ cursor: 'pointer', userSelect: 'none' }}
                >
                  <h3>
                    {accordionOpen.resetActions ? '▼' : '▶'} 🗑️ Reset Actions (Dangerous)
                  </h3>
                </div>
                {accordionOpen.resetActions && (
                  <div className="debug-action-buttons" style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    <button
                      className="reset-button reset-postgres"
                      onClick={handleResetPostgres}
                      disabled={isResettingPostgres}
                      title="Delete all documents and chunks from PostgreSQL"
                    >
                      🗑️ {isResettingPostgres ? "Deleting..." : "Delete Docs from Postgres"}
                    </button>
                    <button
                      className="reset-button reset-qdrant"
                      onClick={handleResetQdrant}
                      disabled={isResettingQdrant}
                      title="Delete all document vectors from Qdrant"
                    >
                      🗑️ {isResettingQdrant ? "Deleting..." : "Delete Docs from Qdrant"}
                    </button>
                    <button
                      className="reset-button reset-cache"
                      onClick={handleResetCache}
                      disabled={isResettingCache}
                      title="Clear all caches (database + memory)"
                      style={{ backgroundColor: '#059669' }}
                    >
                      🗑️ {isResettingCache ? "Clearing..." : "Clear All Caches"}
                    </button>
                  </div>
                )}
              </section>
            </>
          )}
        </div>
    </div>
  );
}
