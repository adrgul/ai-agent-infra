/**
 * MessageBubble component - Displays individual chat messages.
 */
import React from 'react';
import { ChatMessage } from '../types';
import { formatTime } from '../utils';

interface MessageBubbleProps {
  message: ChatMessage;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={`message-container ${isUser ? 'user' : 'assistant'}`}>
      <div className={`message-bubble ${isUser ? 'user-bubble' : 'assistant-bubble'}`}>
        <div className="message-content">{message.content}</div>
        <div className="message-time">{formatTime(message.timestamp)}</div>
        
        {message.toolsUsed && message.toolsUsed.length > 0 && (
          <div className="tools-used">
            <div className="tools-label">🛠️ Tools used:</div>
            {message.toolsUsed.map((tool, idx) => (
              <div key={idx} className="tool-item">
                <span className={`tool-status ${tool.success ? 'success' : 'error'}`}>
                  {tool.success ? '✓' : '✗'}
                </span>
                <span className="tool-name">{tool.name}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
