import React from "react";

export type DebugInfo = {
  request_json: Record<string, unknown>;
  user_id: string;
  session_id: string;
  user_query: string;
  rag_context: Array<Record<string, unknown>> | string[];
  // New: RAG telemetry provides run_id, decision, topk with scores, latencies, config snapshot
  rag_telemetry?: Record<string, any>;
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

      {debug.rag_telemetry && (
        <div className="uk-margin-small">
          <div className="uk-text-meta uk-margin-xsmall-bottom">RAG Telemetry</div>
          <div className="uk-text-small">
            <div>Run ID: {debug.rag_telemetry.run_id}</div>
            <div>Decision: {debug.rag_telemetry.decision}</div>
            <div>Elapsed: {debug.rag_telemetry.elapsed_s?.toFixed(3)}s</div>
            <div>Embed latency: {debug.rag_telemetry.latency_embed_s?.toFixed(3)}s</div>
            <div>Retrieval latency: {debug.rag_telemetry.latency_retrieval_s?.toFixed(3)}s</div>
            <div>Config: {JSON.stringify(debug.rag_telemetry.config_snapshot)}</div>
            <div className="uk-margin-small-top">
              <div className="uk-text-meta">Top-k results</div>
              <table className="uk-table uk-table-divider uk-table-small">
                <thead>
                  <tr>
                    <th>rank</th>
                    <th>id</th>
                    <th>doc</th>
                    <th>sv</th>
                    <th>ss</th>
                    <th>sf</th>
                    <th>excerpt</th>
                  </tr>
                </thead>
                <tbody>
                  {debug.rag_telemetry.topk?.map((t: any, idx: number) => (
                    <Row key={t.id || idx} t={t} idx={idx} />
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
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

const Row: React.FC<{ t: any; idx: number }> = ({ t, idx }) => {
  const [open, setOpen] = React.useState(false);
  return (
    <>
      <tr onClick={() => setOpen(!open)} style={{ cursor: "pointer" }}>
        <td>{idx + 1}</td>
        <td>{t.id}</td>
        <td>{t.metadata?.title || t.metadata?.doc_id || "-"}</td>
        <td>{(t.score_vector || 0).toFixed(3)}</td>
        <td>{(t.score_sparse || 0).toFixed(3)}</td>
        <td>{(t.score_final || 0).toFixed(3)}</td>
        <td>{(t.document || "").slice(0, 120)}</td>
      </tr>
      {open && (
        <tr>
          <td colSpan={7}>
            <pre className="uk-text-small uk-background-muted uk-padding-small">
              {t.document}
            </pre>
          </td>
        </tr>
      )}
    </>
  );
};

export default DebugSidebar;
