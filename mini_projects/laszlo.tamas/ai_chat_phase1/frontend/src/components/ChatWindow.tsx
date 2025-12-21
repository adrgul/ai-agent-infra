import { useEffect, useRef } from "react";
import { Message } from "../types";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  messages: Message[];
}

export const ChatWindow = ({ messages }: ChatWindowProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="empty-state">
          <p>No messages yet. Start a conversation!</p>
        </div>
      ) : (
        messages.map((message, index) => (
          <MessageBubble key={index} message={message} />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  );
};
