import React, { useState } from 'react';
import { WorkflowStateUpdate } from '../hooks/useWorkflowState';

interface WorkflowStateInspectorProps {
  stateHistory: WorkflowStateUpdate[];
  latestState: WorkflowStateUpdate | null;
  currentNode: string | null;
  isConnected: boolean;
}

export const WorkflowStateInspector: React.FC<WorkflowStateInspectorProps> = ({
  stateHistory,
  latestState,
  currentNode,
  isConnected
}) => {
  const [showFullState, setShowFullState] = useState(true);
  const [showDiff, setShowDiff] = useState(false);

  // Get previous state for diff
  const previousState = stateHistory.length > 1 ? stateHistory[stateHistory.length - 2] : null;

  // Compute diff between previous and latest
  const computeDiff = () => {
    if (!previousState || !latestState) return {};
    
    const diff: Record<string, any> = {};
    const prev = previousState.state;
    const curr = latestState.state;
    
    // Check each field for changes
    Object.keys(curr).forEach((key) => {
      if (JSON.stringify(prev[key as keyof typeof prev]) !== JSON.stringify(curr[key as keyof typeof curr])) {
        diff[key] = {
          old: prev[key as keyof typeof prev],
          new: curr[key as keyof typeof curr]
        };
      }
    });
    
    return diff;
  };

  const diff = showDiff ? computeDiff() : {};

  return (
    <div className="workflow-state-inspector">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <h4 className="font-bold text-white">🔄 Workflow State</h4>
          <span className={`text-xs px-2 py-1 rounded ${isConnected ? 'bg-green-700' : 'bg-red-700'}`}>
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          {currentNode && (
            <span className="text-xs px-2 py-1 bg-blue-700 rounded font-mono">
              Node: {currentNode}
            </span>
          )}
        </div>
        
        {/* View toggle buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => { setShowFullState(true); setShowDiff(false); }}
            className={`text-xs px-3 py-1 rounded ${showFullState ? 'bg-blue-600' : 'bg-slate-700'}`}
          >
            Full State
          </button>
          <button
            onClick={() => { setShowFullState(false); setShowDiff(true); }}
            className={`text-xs px-3 py-1 rounded ${showDiff ? 'bg-blue-600' : 'bg-slate-700'}`}
            disabled={!previousState}
          >
            Diff
          </button>
        </div>
      </div>

      {/* Content */}
      {!latestState ? (
        <div className="text-slate-400 text-sm italic p-4 bg-slate-900/50 rounded">
          No workflow state yet. Send a message to see real-time updates.
        </div>
      ) : (
        <div className="max-h-[400px] overflow-y-auto">
          {showFullState && (
            <pre className="text-xs text-slate-200 whitespace-pre-wrap font-mono bg-slate-900/50 p-4 rounded">
              {JSON.stringify(latestState.state, null, 2)}
            </pre>
          )}
          
          {showDiff && (
            <div className="bg-slate-900/50 p-4 rounded space-y-2">
              {Object.keys(diff).length === 0 ? (
                <div className="text-slate-400 text-sm italic">No changes from previous state</div>
              ) : (
                Object.entries(diff).map(([key, value]: [string, any]) => (
                  <div key={key} className="border-l-4 border-yellow-500 pl-3">
                    <div className="text-yellow-300 font-bold text-xs mb-1">{key}</div>
                    <div className="text-xs">
                      <div className="text-red-400">
                        <span className="font-bold">- </span>
                        {JSON.stringify(value.old)}
                      </div>
                      <div className="text-green-400">
                        <span className="font-bold">+ </span>
                        {JSON.stringify(value.new)}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}

      {/* Timeline */}
      {stateHistory.length > 0 && (
        <div className="mt-4 pt-4 border-t border-slate-700">
          <h5 className="text-xs font-bold text-slate-400 mb-2">Execution Timeline ({stateHistory.length} steps)</h5>
          <div className="space-y-1 max-h-[150px] overflow-y-auto">
            {stateHistory.map((update, idx) => (
              <div key={idx} className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">{idx + 1}.</span>
                <span className="font-mono text-blue-300">{update.node}</span>
                <span className="text-slate-400">
                  {new Date(update.timestamp).toLocaleTimeString()}
                </span>
                {update.state.next_action && (
                  <span className="px-2 py-0.5 bg-purple-700 rounded text-[10px]">
                    → {update.state.next_action}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
