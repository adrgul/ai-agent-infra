import React from 'react';

interface ChatMessage {
  role: string;
  content: string;
}

interface ActualLLMMessage {
  type: string;  // "SystemMessage", "HumanMessage", "AIMessage"
  content: string;
}

interface PromptDetails {
  system_prompt?: string;
  chat_history?: ChatMessage[];
  current_query?: string;
  cache_source?: string;
  user_firstname?: string;
  user_lastname?: string;
  chat_history_count?: number;
  actions_taken?: string[];
  short_term_memory_messages?: number;
  short_term_memory_scope?: string;
  actual_llm_messages?: ActualLLMMessage[];
}

interface PromptInspectorProps {
  promptDetails: PromptDetails | null;
  isOpen: boolean;
  onClose: () => void;
}

export const PromptInspector: React.FC<PromptInspectorProps> = ({ promptDetails, isOpen, onClose }) => {
  if (!isOpen || !promptDetails) return null;

  // DEBUG: Console log what we received
  console.log("🔍 PromptInspector RENDER:", promptDetails);

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-lg w-full max-w-6xl max-h-[90vh] flex flex-col shadow-2xl">
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700 bg-slate-900">
          <div>
            <h2 className="text-xl font-bold text-white">🔍 LLM Prompt Inspector</h2>
            <div className="flex gap-4 mt-1 text-xs text-slate-400">
              {promptDetails.cache_source && (
                <span>Cache: {promptDetails.cache_source === 'memory' ? '🟢 Memory' : promptDetails.cache_source === 'database' ? '🟡 Database' : '🔵 Fresh'}</span>
              )}
              {promptDetails.user_firstname && (
                <span>User: {promptDetails.user_firstname} {promptDetails.user_lastname}</span>
              )}
              {promptDetails.chat_history_count !== undefined && (
                <span>History: {promptDetails.chat_history_count} messages</span>
              )}
            </div>
            <div className="flex gap-4 mt-1 text-xs text-amber-300 font-mono">
              {promptDetails.short_term_memory_messages !== undefined && (
                <span>📦 SHORT_TERM_MEMORY_MESSAGES = {promptDetails.short_term_memory_messages}</span>
              )}
              {promptDetails.short_term_memory_scope && (
                <span>🎯 SHORT_TERM_MEMORY_SCOPE = {promptDetails.short_term_memory_scope}</span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-2xl px-3 py-1 hover:bg-slate-700 rounded"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          
          {/* 1. System Prompt */}
          <div className="bg-blue-900/20 border-l-4 border-blue-500 rounded">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-blue-400 font-bold text-lg">📋 1. System Prompt</span>
                  <span className="text-xs text-slate-400">(egyesített: Application + Tenant + User)</span>
                </div>
                <span className="text-xs text-blue-300 font-mono">
                  {promptDetails.system_prompt?.length || 0} chars
                </span>
              </div>
              <pre className="text-sm text-blue-200 whitespace-pre-wrap font-mono bg-slate-900/50 p-4 rounded max-h-[400px] overflow-y-auto">
                {promptDetails.system_prompt || 'Nincs system prompt'}
              </pre>
            </div>
          </div>

          {/* 2. Chat History (Context) */}
          <div className="bg-purple-900/20 border-l-4 border-purple-500 rounded">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-purple-400 font-bold text-lg">💬 2. Chat History (Context)</span>
                  <span className="text-xs text-slate-400">(utolsó {promptDetails.chat_history?.length || 0} üzenet)</span>
                </div>
              </div>
              {promptDetails.chat_history && promptDetails.chat_history.length > 0 ? (
                <div className="space-y-2 bg-slate-900/50 p-4 rounded max-h-[300px] overflow-y-auto">
                  {promptDetails.chat_history.map((msg, idx) => (
                    <div key={idx} className={`p-2 rounded ${msg.role === 'user' ? 'bg-purple-800/30' : 'bg-slate-700/30'}`}>
                      <div className="text-xs text-purple-300 font-bold mb-1">
                        {msg.role === 'user' ? '👤 User' : '🤖 Assistant'}:
                      </div>
                      <div className="text-sm text-purple-200 font-mono whitespace-pre-wrap">
                        {msg.content}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-purple-300 bg-slate-900/50 p-4 rounded italic">
                  Nincs előzetes chat history (első üzenet a session-ben)
                </div>
              )}
            </div>
          </div>

          {/* 3. Current Query */}
          <div className="bg-green-900/20 border-l-4 border-green-500 rounded">
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-green-400 font-bold text-lg">✍️ 3. Current User Message</span>
                  <span className="text-xs text-slate-400">(aktuális query)</span>
                </div>
                <span className="text-xs text-green-300 font-mono">
                  {promptDetails.current_query?.length || 0} chars
                </span>
              </div>
              <pre className="text-sm text-green-200 whitespace-pre-wrap font-mono bg-slate-900/50 p-4 rounded">
                {promptDetails.current_query || 'Nincs query'}
              </pre>
            </div>
          </div>

          {/* Actions Badge */}
          {promptDetails.actions_taken && promptDetails.actions_taken.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap p-4 bg-slate-900/50 rounded border border-slate-700">
              <span className="text-sm text-slate-400 font-bold">Workflow actions:</span>
              {promptDetails.actions_taken.map((action, idx) => (
                <span key={idx} className="px-3 py-1 bg-orange-700/50 text-orange-200 rounded-full text-xs font-mono">
                  {action}
                </span>
              ))}
            </div>
          )}

          {/* ACTUAL LLM Messages - RAW */}
          {promptDetails.actual_llm_messages && promptDetails.actual_llm_messages.length > 0 && (
            <div className="bg-red-900/20 border-l-4 border-red-500 rounded">
              <div className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-red-400 font-bold text-lg">⚠️ ACTUAL LLM INPUT (RAW)</span>
                    <span className="text-xs text-slate-400">{promptDetails.actual_llm_messages.length} messages</span>
                  </div>
                </div>
                <div className="space-y-2 bg-slate-900/50 p-4 rounded max-h-[400px] overflow-y-auto">
                  {promptDetails.actual_llm_messages.map((msg, idx) => (
                    <div key={idx} className={`p-3 rounded border-l-4 ${
                      msg.type === 'SystemMessage' ? 'bg-blue-900/30 border-blue-500' :
                      msg.type === 'HumanMessage' ? 'bg-purple-900/30 border-purple-500' :
                      'bg-slate-700/30 border-slate-500'
                    }`}>
                      <div className="text-xs font-bold mb-1 text-amber-300 flex justify-between">
                        <span>{idx}. {msg.type}</span>
                        <span className="text-slate-400">{msg.content.length} chars</span>
                      </div>
                      <pre className="text-sm text-slate-200 whitespace-pre-wrap font-mono">
                        {msg.content}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-700 p-4 bg-slate-900 flex justify-between items-center">
          <div className="text-xs text-slate-400">
            <strong>ACTUAL LLM INPUT:</strong> {promptDetails.actual_llm_messages?.length || '?'} messages
          </div>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium"
          >
            Bezárás
          </button>
        </div>
      </div>
    </div>
  );
};
