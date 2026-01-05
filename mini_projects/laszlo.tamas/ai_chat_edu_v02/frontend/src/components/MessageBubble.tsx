import { Message } from "../types";

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === "user";
  
  const formatResponseTime = (ms: number) => {
    if (ms < 1000) {
      return `${ms}ms`;
    }
    return `${(ms / 1000).toFixed(2)}s`;
  };
  
  return (
    <div className={`message-bubble ${isUser ? "user-message" : "assistant-message"}`}>
      <div className="message-role">{message.role}</div>
      <div className="message-content">{message.content}</div>
      {message.sources && message.sources.length > 0 && (
        <div className="message-sources">
          📚 Források: {message.sources.map((source, idx) => (
            <span key={idx} className="source-badge" title={`Document ID: ${source.id}`}>
              {source.title}
            </span>
          ))}
          {message.ragParams && (
            <span className="rag-params" style={{ marginLeft: '10px', fontSize: '0.85em', color: '#666' }}>
              (TOP_K={message.ragParams.top_k}, MIN_SCORE={message.ragParams.min_score_threshold})
            </span>
          )}
        </div>
      )}
      <div className="message-timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
        {message.responseTime && (
          <span className="response-timer"> • {formatResponseTime(message.responseTime)}</span>
        )}
      </div>
    </div>
  );
};
