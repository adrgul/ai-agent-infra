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
          <div className="prompt-item-new"><b>A Gáztörvénnyel kapcsolatban induló kérdések:</b></div>
          <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Mi a Gáztörvény célja?"</div>
          <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Listázd, hogy mely paragrafusok foglalkoznak az egyetemes szolgáltatóval"</div>
          <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Hány fajta engedély típus létezik?"</div>
          <div className="prompt-item-new">&nbsp;&nbsp;&nbsp;&nbsp;• "Mire van felhatalmazása a MEKH-nek (Hivatal) és mely pontok szerint?"</div>
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
