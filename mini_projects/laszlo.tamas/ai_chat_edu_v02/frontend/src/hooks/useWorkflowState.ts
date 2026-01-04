import { useEffect, useState, useRef } from 'react';

export interface WorkflowStateUpdate {
  type: 'workflow_state_update';
  node: string;
  state: {
    query?: string;
    session_id?: string;
    next_action?: string;
    iteration_count?: number;
    actions_taken?: string[];
    retrieved_chunks_count?: number;
    listed_documents_count?: number;
    intermediate_results_count?: number;
    system_prompt_cached?: boolean;
    cache_source?: string;
    error?: string;
  };
  timestamp: string;
}

interface UseWorkflowStateOptions {
  enabled: boolean;  // Only connect when enabled
  sessionId: string | null;
}

export function useWorkflowState({ enabled, sessionId }: UseWorkflowStateOptions) {
  const [stateHistory, setStateHistory] = useState<WorkflowStateUpdate[]>([]);
  const [latestState, setLatestState] = useState<WorkflowStateUpdate | null>(null);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Only connect if enabled and sessionId exists
    if (!enabled || !sessionId) {
      // Cleanup existing connection
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setIsConnected(false);
      return;
    }

    // Create WebSocket connection
    // Extract base URL from API URL (remove /api suffix if present)
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:18000/api';
    const baseUrl = apiUrl.replace('/api', '').replace('http://', '').replace('https://', '');
    const wsUrl = `ws://${baseUrl}/ws/workflow/${sessionId}`;
    console.log(`🔌 Connecting to workflow WebSocket: ${wsUrl}`);
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Workflow WebSocket connected');
      setIsConnected(true);
      
      // Send ping to keep alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);  // Every 30 seconds

      // Store interval for cleanup
      (ws as any)._pingInterval = pingInterval;
    };

    ws.onmessage = (event) => {
      try {
        const data: WorkflowStateUpdate = JSON.parse(event.data);
        
        if (data.type === 'workflow_state_update') {
          // Add timestamp
          data.timestamp = new Date().toISOString();
          
          console.log(`📊 Workflow state update [${data.node}]:`, data.state);
          
          setLatestState(data);
          setCurrentNode(data.node);
          setStateHistory((prev) => [...prev, data]);
        }
      } catch (error) {
        console.error('Failed to parse workflow state message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('❌ Workflow WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('🔌 Workflow WebSocket disconnected');
      setIsConnected(false);
      
      // Clear ping interval
      if ((ws as any)._pingInterval) {
        clearInterval((ws as any)._pingInterval);
      }
    };

    // Cleanup on unmount or dependency change
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      if ((ws as any)._pingInterval) {
        clearInterval((ws as any)._pingInterval);
      }
    };
  }, [enabled, sessionId]);

  const clearHistory = () => {
    setStateHistory([]);
    setLatestState(null);
    setCurrentNode(null);
  };

  return {
    stateHistory,
    latestState,
    currentNode,
    isConnected,
    clearHistory
  };
}
