import { useState } from 'react'
import axios from 'axios'
import styles from '../styles/Home.module.css'

interface Citation {
  doc_id: string
  title: string
  score: number
  snippet?: string
  url?: string
  source?: string
}

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  tool_used?: string
  domain?: string
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim() || loading) return

    const userMessage: ChatMessage = {
      role: 'user',
      content: input
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await axios.post('http://localhost:8000/api/chat', {
        message: input,
        session_id: 'session_123'
      })

      const assistantMessage: ChatMessage = {
        role: 'assistant',
        content: response.data.response,
        citations: response.data.citations,
        tool_used: response.data.tool_used,
        domain: response.data.domain
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Hiba történt a válasz generálása során. Kérlek próbáld újra.'
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <main className={styles.main}>
        <h1 className={styles.title}>Knowledge Router</h1>
        
        <div className={styles.chatContainer}>
          <div className={styles.messages}>
            {messages.length === 0 && (
              <div className={styles.welcome}>
                <p>Üdvözöllek a Knowledge Router-ban!</p>
                <p>Kérdezz bármit a HR vagy IT dokumentációról.</p>
              </div>
            )}
            {messages.map((msg, idx) => (
              <div key={idx} className={styles[msg.role]}>
                <div className={styles.messageContent}>
                  <strong>{msg.role === 'user' ? 'Te' : 'Assistant'}:</strong>
                  <p>{msg.content}</p>
                  {msg.citations && msg.citations.length > 0 && (
                    <div className={styles.citations}>
                      <strong>Források ({msg.citations.length}):</strong>
                      {msg.citations.map((cite, i) => (
                        <div key={cite.doc_id || i} className={styles.citation}>
                          <div className={styles.citationHeader}>
                            <a 
                              href={cite.url || cite.source || '#'} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className={styles.citationLink}
                            >
                              {cite.title}
                            </a>
                            {cite.score && (
                              <span className={styles.score}>
                                {(cite.score * 100).toFixed(0)}%
                              </span>
                            )}
                          </div>
                          {cite.snippet && (
                            <div className={styles.snippet}>
                              {cite.snippet}
                            </div>
                          )}
                          {cite.source && (
                            <div className={styles.source}>
                              <small>Forrás: {cite.source}</small>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  {msg.tool_used && (
                    <div className={styles.tool}>
                      <small>Használt eszköz: {msg.tool_used}</small>
                    </div>
                  )}
                  {msg.domain && (
                    <div className={styles.domain}>
                      <small>Domain: {msg.domain}</small>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className={styles.assistant}>
                <div className={styles.messageContent}>
                  <p>Válasz generálása...</p>
                </div>
              </div>
            )}
          </div>

          <div className={styles.inputContainer}>
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Írd be a kérdésed..."
              className={styles.input}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={loading || !input.trim()}
              className={styles.button}
            >
              Küldés
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}

