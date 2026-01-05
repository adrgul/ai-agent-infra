/**
 * Utility functions.
 */

/**
 * Generate a stable user ID (stored in localStorage).
 */
export function getUserId(): string {
  const KEY = 'ai_agent_user_id';
  let userId = localStorage.getItem(KEY);
  
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(KEY, userId);
  }
  
  return userId;
}

/**
 * Generate a stable session ID (stored in localStorage).
 */
export function getSessionId(): string {
  const KEY = 'ai_agent_session_id';
  let sessionId = localStorage.getItem(KEY);
  
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem(KEY, sessionId);
  }
  
  return sessionId;
}

/**
 * Reset session ID (for reset context).
 */
export function resetSessionId(): void {
  const sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  localStorage.setItem('ai_agent_session_id', sessionId);
}

/**
 * Format date for display.
 */
export function formatTime(date: Date): string {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}
