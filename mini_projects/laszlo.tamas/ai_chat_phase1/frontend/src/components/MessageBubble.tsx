import { Message } from "../types";

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.role === "user";
  
  return (
    <div className={`message-bubble ${isUser ? "user-message" : "assistant-message"}`}>
      <div className="message-role">{message.role}</div>
      <div className="message-content">{message.content}</div>
      <div className="message-timestamp">
        {new Date(message.timestamp).toLocaleTimeString()}
      </div>
    </div>
  );
};
