import React from "react";

export type DebugInfo = {
  request_json: Record<string, unknown>;
  user_id: string;
  session_id: string;
  user_query: string;
  rag_context: string[];
  final_llm_prompt: string;
};

type Props = {
  debug?: DebugInfo;
};

const DebugSidebar: React.FC<Props> = ({ debug }) => {
  if (!debug) {
    return (
      <div className="sidebar">
        <h4 className="uk-text-bold uk-margin-small-bottom">Debug</h4>
        <p className="uk-text-meta">Send a message to see request details.</p>
      </div>
    );
  }

  return (
    <div className="sidebar">
      <div className="uk-flex uk-flex-between uk-flex-middle uk-margin-small-bottom">
        <h4 className="uk-text-bold uk-margin-remove">Debug</h4>
        <span className="uk-badge">Read-only</span>
      </div>
      <div className="uk-margin-small">
        <div className="uk-text-meta uk-margin-xsmall-bottom">User ID</div>
        <div className="uk-text-small uk-text-bold">{debug.user_id}</div>
      </div>
      <div className="uk-margin-small">
        <div className="uk-text-meta uk-margin-xsmall-bottom">Session ID</div>
        <div className="uk-text-small uk-text-bold">{debug.session_id}</div>
      </div>
      <div className="uk-margin-small">
        <div className="uk-text-meta uk-margin-xsmall-bottom">User Query</div>
        <div className="uk-text-small">{debug.user_query}</div>
      </div>
      <div className="uk-margin-small">
        <div className="uk-text-meta uk-margin-xsmall-bottom">RAG Context</div>
        <pre className="uk-text-small">
          {debug.rag_context && debug.rag_context.length > 0
            ? JSON.stringify(debug.rag_context, null, 2)
            : "[]"}
        </pre>
      </div>
      <div className="uk-margin-small">
        <div className="uk-text-meta uk-margin-xsmall-bottom">Final LLM Prompt</div>
        <pre className="uk-text-small">{debug.final_llm_prompt}</pre>
      </div>
      <div className="uk-margin-small">
        <div className="uk-text-meta uk-margin-xsmall-bottom">Request JSON</div>
        <pre className="uk-text-small">
          {JSON.stringify(debug.request_json, null, 2)}
        </pre>
      </div>
    </div>
  );
};

export default DebugSidebar;
