/**
 * ChatWindow component - Displays the conversation history.
 */
import React, { useEffect, useRef } from 'react';
import { ChatMessage } from '../types';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ messages, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  return (
    <div className="chat-window">
      {messages.length === 0 ? (
        <div className="welcome-message">
          <h2>Welcome to AI Agent Demo</h2>
          <p>Ask me about weather, cryptocurrency prices, currency exchange, or anything else!</p>
          <div className="example-prompts">
            <div className="prompt-label">Try these:</div>
            <div className="prompt-item">• What's the weather in Budapest?</div>
            <div className="prompt-item">• What's the current BTC price in EUR?</div>
            <div className="prompt-item">• Convert 100 EUR to HUF</div>
            <div className="prompt-item">• From now on, answer in English</div>
            <div className="prompt-item-new">• New feature: Radio API, try these questions</div>
            <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "What are the most popular radio stations?"</div>
            <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Find radio stations in German language"</div>
            <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Search for BBC radio"</div>
            <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Find rock stations from the USA"</div>
            <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Show me tags related to electronic music"</div>

          </div>
        </div>
      ) : (
        <>
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {isLoading && (
            <div className="message-container assistant">
              <div className="message-bubble assistant-bubble loading">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </>
      )}
    </div>
  );
};
