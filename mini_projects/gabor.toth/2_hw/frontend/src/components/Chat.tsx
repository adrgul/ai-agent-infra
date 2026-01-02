import React, { useState, useEffect, useRef } from 'react';
import { chatAPI, Message } from '../api';
import { useActivity } from '../contexts/ActivityContext';
import { CitationModal } from './CitationModal';
import '../styles/chat.css';

interface ChatProps {
  userId: string;
  sessionId: string;
  onDebugInfo?: (info: any) => void;
}

interface MessageWithFallback extends Message {
  fallback_search?: boolean;
}

interface Citation {
  chunk_id: string;
  content: string;
  source_file: string;
  section_title: string;
  distance: number;
}

interface ChatResponse {
  final_answer: string;
  memory_snapshot: any;
  fallback_search?: boolean;
  rag_debug?: {
    retrieved: Citation[];
  };
}

export const Chat: React.FC<ChatProps> = ({ userId, sessionId, onDebugInfo }) => {
  const { addActivity } = useActivity();
  const [messages, setMessages] = useState<MessageWithFallback[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const [citationMap, setCitationMap] = useState<Record<string, Citation>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || loading) return;

    const userMessage = inputValue.trim();
    setInputValue('');
    setLoading(true);

    // Add user message to chat immediately
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: userMessage,
        timestamp: new Date().toISOString(),
        metadata: {},
      },
    ]);

    const activityId = addActivity(`💬 Kérdés: "${userMessage}"`, 'info');

    try {
      addActivity('🔍 Kategória felismerés...', 'processing');
      addActivity('📚 Dokumentumok keresése...', 'processing');
      addActivity('🤖 OpenAI API hívása...', 'processing');
      
      const response = await chatAPI.sendMessage(userId, sessionId, userMessage) as ChatResponse;

      // Build citation map for quick lookup
      const newCitationMap: Record<string, Citation> = {};
      if (response.rag_debug?.retrieved) {
        response.rag_debug.retrieved.forEach((chunk, idx) => {
          newCitationMap[String(idx + 1)] = chunk;
        });
      }
      setCitationMap(newCitationMap);

      // Add assistant message
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: response.final_answer,
          timestamp: new Date().toISOString(),
          metadata: {
            category_routed: response.memory_snapshot.routed_category,
          },
          fallback_search: response.fallback_search,
        },
      ]);

      addActivity(`✓ Válasz generálva a "${response.memory_snapshot.routed_category}" kategóriából`, 'success');

      // Trigger debug info if callback provided
      if (onDebugInfo) {
        onDebugInfo({
          routed_category: response.memory_snapshot.routed_category,
          retrieved: response.rag_debug?.retrieved || [],
          fallback_search: response.fallback_search,
        });
      }
    } catch (error: any) {
      addActivity(`✗ Hiba: ${error.message}`, 'error');
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Hiba: ${error.message}`,
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const renderMessageContent = (content: string) => {
    // Parse and render citations as clickable links
    const citationPattern = /\[(\d+)\.\s+forrás\]/g;
    const parts = content.split(citationPattern);
    
    return (
      <>
        {parts.map((part, idx) => {
          // Even indices are regular text, odd indices are citation numbers
          if (idx % 2 === 0) {
            return <span key={idx}>{part}</span>;
          } else {
            const citationNum = part;
            const citation = citationMap[citationNum];
            return (
              <button
                key={idx}
                className="citation-link"
                onClick={() => citation && setSelectedCitation(citation)}
                title={citation ? `${citation.source_file}` : 'Citation not found'}
              >
                [{citationNum}. forrás]
              </button>
            );
          }
        })}
      </>
    );
  };

  return (
    <div className="chat-container">
      <CitationModal 
        isOpen={!!selectedCitation} 
        citation={selectedCitation} 
        onClose={() => setSelectedCitation(null)} 
      />
      
      <div className="messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>Üdvözöljük! Töltsenek fel dokumentumokat a bal oldali panelből, majd kérdezzen rá őkre.</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.role}`}>
            <div className="message-content">
              {msg.role === 'assistant' ? renderMessageContent(msg.content) : msg.content}
            </div>
            {msg.metadata?.category_routed && !msg.fallback_search && (
              <div className="message-meta">
                Kategória: {msg.metadata.category_routed}
              </div>
            )}
            {msg.fallback_search && (
              <div className="message-meta fallback-indicator">
                ℹ️ Minden dokumentumban kerestem (az eredeti kategóriában nem volt dokumentum)
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <div className="input-area">
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="Írjon egy kérdést..."
          disabled={loading}
        />
        <button onClick={handleSendMessage} disabled={loading}>
          {loading ? 'Feldolgozás...' : 'Küldés'}
        </button>
        <button 
          onClick={() => setInputValue('reset context (Amennyiben tényleg törölni akarod az előzményeket, kattints a Küldés gombra)')} 
          className="reset-btn"
        >
          Kontextus törlés
        </button>
      </div>
    </div>
  );
};
