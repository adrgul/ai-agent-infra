import React from "react";

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
};

type Props = {
  messages: ChatMessage[];
  input: string;
  loading: boolean;
  onInputChange: (value: string) => void;
  onSend: () => void;
};

const ChatPanel: React.FC<Props> = ({
  messages,
  input,
  loading,
  onInputChange,
  onSend,
}) => {
  return (
    <div className="chat-panel uk-padding">
      <div className="uk-flex uk-flex-between uk-flex-middle uk-margin-small-bottom">
        <div>
          <h3 className="uk-margin-remove">KnowledgeRouter</h3>
          <p className="uk-text-meta uk-margin-remove">
            LangGraph-orchestrated chat · Docker-ready
          </p>
        </div>

      </div>
      <div
        className="uk-margin uk-height-medium uk-overflow-auto"
        data-testid="chat-history"
      >
        {messages.length === 0 && (
          <div className="uk-text-meta">Start the conversation.</div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={`${msg.role}-${idx}`}
            className={`message-bubble ${
              msg.role === "user" ? "bubble-user" : "bubble-assistant"
            }`}
          >
            <div className="uk-text-meta uk-margin-xsmall-bottom">
              {msg.role === "user" ? "You" : "Assistant"}
            </div>
            <div>{msg.content}</div>
          </div>
        ))}
      </div>
      <div className="uk-margin">
        <div className="uk-flex uk-flex-middle" data-testid="chat-input">
          <textarea
            className="uk-textarea"
            placeholder='Ask anything... or type "reset context"'
            rows={3}
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
            disabled={loading}
          />
        </div>
        <div className="uk-flex uk-flex-right uk-margin-small-top">
          <button
            className="uk-button uk-button-primary"
            onClick={onSend}
            disabled={loading || !input.trim()}
          >
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
