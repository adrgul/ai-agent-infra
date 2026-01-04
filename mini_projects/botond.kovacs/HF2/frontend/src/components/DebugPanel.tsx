/**
 * DebugPanel component - Shows tools used and memory snapshot.
 */
import React from 'react';
import { MemorySnapshot, ToolUsed } from '../types';

interface DebugPanelProps {
  toolsUsed: ToolUsed[];
  memorySnapshot: MemorySnapshot | null;
  isOpen: boolean;
  onToggle: () => void;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({
  toolsUsed,
  memorySnapshot,
  isOpen,
  onToggle,
}) => {
  return (
    <>
      <button className="debug-toggle" onClick={onToggle}>
        {isOpen ? '✕ Close Debug' : '🔧 Debug Panel'}
      </button>
      
      {isOpen && (
        <div className="debug-panel">
          <h3>Debug Information</h3>
          
          <div className="debug-section">
            <h4>Last Tools Used ({toolsUsed.length})</h4>
            {toolsUsed.length === 0 ? (
              <div className="debug-empty">No tools used</div>
            ) : (
              <div className="tools-list">
                {toolsUsed.map((tool, idx) => (
                  <div key={idx} className="debug-tool">
                    <div className="debug-tool-name">
                      <span className={`status-icon ${tool.success ? 'success' : 'error'}`}>
                        {tool.success ? '✓' : '✗'}
                      </span>
                      {tool.name}
                    </div>
                    <pre className="debug-args">
                      {JSON.stringify(tool.arguments, null, 2)}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="debug-section">
            <h4>Memory Snapshot</h4>
            {memorySnapshot ? (
              <div>
                <div className="debug-subsection">
                  <strong>Preferences:</strong>
                  <pre>{JSON.stringify(memorySnapshot.preferences, null, 2)}</pre>
                </div>
                
                <div className="debug-subsection">
                  <strong>Workflow State:</strong>
                  <pre>{JSON.stringify(memorySnapshot.workflow_state, null, 2)}</pre>
                </div>
                
                <div className="debug-subsection">
                  <strong>Message Count:</strong> {memorySnapshot.message_count}
                </div>
              </div>
            ) : (
              <div className="debug-empty">No memory snapshot available</div>
            )}
          </div>
        </div>
      )}
    </>
  );
};
