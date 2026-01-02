import React, { useState, useEffect } from 'react';
import { getCacheStats, clearAllCaches, CacheStats } from '../api';

const AUTO_REFRESH_INTERVAL = 5000; // 5 seconds

export const CacheDebugSection: React.FC = () => {
  const [stats, setStats] = useState<CacheStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  // Fetch cache stats
  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getCacheStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch cache stats');
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh every 5 seconds
  useEffect(() => {
    if (isOpen) {
      fetchStats(); // Initial fetch when opened

      if (autoRefresh) {
        const interval = setInterval(fetchStats, AUTO_REFRESH_INTERVAL);
        return () => clearInterval(interval);
      }
    }
  }, [autoRefresh, isOpen]);

  // Clear all caches
  const handleClearCache = async () => {
    if (!window.confirm('⚠️ Clear ALL caches? This will delete memory + DB cache entries.')) {
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await clearAllCaches();
      setSuccess(
        `✅ Caches cleared! Memory: ${result.memory_cleared ? 'Yes' : 'No'}, DB: ${result.db_cleared} entries`
      );
      // Refresh stats after clearing
      setTimeout(fetchStats, 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to clear caches');
    } finally {
      setLoading(false);
    }
  };

  // Close success banner after 3 seconds
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 3000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  return (
    <section className="debug-section">
      <div
        className="debug-accordion-header"
        onClick={() => setIsOpen(!isOpen)}
        style={{ cursor: 'pointer', userSelect: 'none' }}
      >
        <h3>
          {isOpen ? '▼' : '▶'} 🗄️ Cache Statistics
          {stats && (
            <span style={{ fontSize: '12px', color: '#666', marginLeft: '10px' }}>
              Memory: {stats.memory_cache.size} | DB: {stats.db_cache.cached_users} users
            </span>
          )}
        </h3>
      </div>

      {isOpen && (
        <div style={{ marginTop: '10px' }}>
          {/* Auto-refresh toggle & Refresh button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
            <label className="auto-refresh-toggle">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              {autoRefresh ? "Auto-refresh (5s)" : "Auto-refresh OFF"}
            </label>
            <button
              className="refresh-button"
              onClick={fetchStats}
              disabled={loading}
              title="Refresh cache stats"
            >
              🔄 {loading ? "Loading..." : "Refresh Now"}
            </button>
          </div>

          {/* Success/Error messages */}
          {success && (
            <div className="debug-success-banner" style={{ marginBottom: '15px' }}>
              {success}
              <button onClick={() => setSuccess(null)} style={{ marginLeft: 'auto' }}>×</button>
            </div>
          )}
          {error && (
            <div className="debug-error-banner" style={{ marginBottom: '15px' }}>
              {error}
              <button onClick={() => setError(null)} style={{ marginLeft: 'auto' }}>×</button>
            </div>
          )}

          {loading && !stats ? (
            <div className="debug-loading">Loading cache statistics...</div>
          ) : stats ? (
            <div className="debug-cache-stats">
              {/* Memory Cache (Tier 1) */}
              <div className="cache-tier-box">
                <div className="cache-tier-header">
                  <span className={stats.memory_cache.enabled ? 'status-enabled' : 'status-disabled'}>
                    {stats.memory_cache.enabled ? '✅' : '❌'}
                  </span>
                  <strong>Tier 1: Memory Cache</strong>
                </div>
                {stats.memory_cache.enabled && (
                  <div className="cache-tier-details">
                    <div><strong>Entries:</strong> {stats.memory_cache.size}</div>
                    <div><strong>TTL:</strong> {stats.memory_cache.ttl_seconds}s ({Math.floor(stats.memory_cache.ttl_seconds / 60)} min)</div>
                    <div><strong>Debug Mode:</strong> {stats.memory_cache.debug_mode ? 'ON' : 'OFF'}</div>
                    {stats.memory_cache.keys.length > 0 && (
                      <div title={stats.memory_cache.keys.join(', ')}>
                        <strong>Keys:</strong> {stats.memory_cache.keys.slice(0, 3).join(', ')}
                        {stats.memory_cache.keys.length > 3 && ` +${stats.memory_cache.keys.length - 3} more`}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* PostgreSQL Cache (Tier 2) */}
              <div className="cache-tier-box">
                <div className="cache-tier-header">
                  <span className={stats.db_cache.enabled ? 'status-enabled' : 'status-disabled'}>
                    {stats.db_cache.enabled ? '✅' : '❌'}
                  </span>
                  <strong>Tier 2: PostgreSQL Cache</strong>
                </div>
                {stats.db_cache.enabled && (
                  <div className="cache-tier-details">
                    <div><strong>Cached Users:</strong> {stats.db_cache.cached_users}</div>
                    <div><strong>Total Entries:</strong> {stats.db_cache.total_entries}</div>
                    {stats.db_cache.error && (
                      <div style={{ color: '#d32f2f', marginTop: '8px' }}>
                        ⚠️ Error: {stats.db_cache.error}
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Configuration Flags */}
              <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #e0e0e0' }}>
                <div style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>
                  <strong>Configuration (system.ini):</strong>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  <span className={`config-chip ${stats.config.memory_enabled ? 'enabled' : 'disabled'}`}>
                    Memory: {stats.config.memory_enabled ? 'ON' : 'OFF'}
                  </span>
                  <span className={`config-chip ${stats.config.db_enabled ? 'enabled' : 'disabled'}`}>
                    DB: {stats.config.db_enabled ? 'ON' : 'OFF'}
                  </span>
                  <span className={`config-chip ${stats.config.browser_enabled ? 'enabled' : 'disabled'}`}>
                    Browser: {stats.config.browser_enabled ? 'ON' : 'OFF'}
                  </span>
                  <span className={`config-chip ${stats.config.llm_enabled ? 'enabled' : 'disabled'}`}>
                    LLM: {stats.config.llm_enabled ? 'ON' : 'OFF'}
                  </span>
                </div>
              </div>

              {/* Actions */}
              <div style={{ marginTop: '15px', paddingTop: '15px', borderTop: '1px solid #e0e0e0' }}>
                <button
                  className="reset-button reset-cache"
                  onClick={handleClearCache}
                  disabled={loading}
                  style={{ backgroundColor: '#d32f2f' }}
                >
                  🗑️ {loading ? "Clearing..." : "Clear All Caches"}
                </button>
              </div>

              {/* Timestamp */}
              <div style={{ marginTop: '10px', fontSize: '11px', color: '#999' }}>
                Last updated: {new Date(stats.timestamp).toLocaleTimeString()}
              </div>
            </div>
          ) : null}
        </div>
      )}
    </section>
  );
};
