import { useState, useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { User, Message } from "./types";
import { fetchUsers, sendChatMessage, fetchSessionMessages } from "./api";
import { UserDropdown } from "./components/UserDropdown";
import { ChatWindow } from "./components/ChatWindow";
import { ChatInput, ChatInputRef } from "./components/ChatInput";
import { DebugModal } from "./components/DebugModal";
import { HowTo } from "./components/HowTo";
import "./App.css";

function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDebugOpen, setIsDebugOpen] = useState(false);
  const chatInputRef = useRef<ChatInputRef>(null);

  // Load users on mount
  useEffect(() => {
    fetchUsers()
      .then(setUsers)
      .catch((err) => {
        console.error("Failed to load users:", err);
        setError("Failed to load users. Please refresh the page.");
      });
  }, []);

  // Handle user change
  const handleUserChange = async (userId: number) => {
    setSelectedUserId(userId);
    const storedSessionId = localStorage.getItem(`sessionId_${userId}`);
    let sessionIdToUse: string;
    if (!storedSessionId) {
      sessionIdToUse = uuidv4();
      localStorage.setItem(`sessionId_${userId}`, sessionIdToUse);
    } else {
      sessionIdToUse = storedSessionId;
    }
    setSessionId(sessionIdToUse);
    setError(null);

    // Load previous messages if session exists
    if (storedSessionId) {
      try {
        const previousMessages = await fetchSessionMessages(storedSessionId);
        setMessages(previousMessages);
      } catch (err) {
        console.error("Failed to load previous messages:", err);
        setMessages([]);
      }
    } else {
      setMessages([]);
    }
  };

  // Handle sending a message
  const handleSendMessage = async (messageContent: string) => {
    if (!selectedUserId || !sessionId) return;

    // Add user message to UI
    const userMessage: Message = {
      role: "user",
      content: messageContent,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage({
        user_id: selectedUserId,
        session_id: sessionId,
        message: messageContent,
      });

      // Add assistant message to UI
      const assistantMessage: Message = {
        role: "assistant",
        content: response.answer,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      
      // Focus the input after assistant response
      setTimeout(() => {
        chatInputRef.current?.focus();
      }, 100);
    } catch (err) {
      console.error("Failed to send message:", err);
      const errorMsg = err instanceof Error ? err.message : "Failed to send message";
      setError(errorMsg);
      
      // Add error message to chat
      const errorMessage: Message = {
        role: "assistant",
        content: `Error: ${errorMsg}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const selectedUser = users.find((u) => u.user_id === selectedUserId);

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Chat - Phase 1</h1>
        <UserDropdown
          users={users}
          selectedUserId={selectedUserId}
          onUserChange={handleUserChange}
        />
      </header>

      {selectedUserId && (
        <button 
          className="debug-button" 
          onClick={() => setIsDebugOpen(true)}
          title="Debug információk"
        >
          🐛 Debug
        </button>
      )}

      {error && <div className="error-banner">{error}</div>}

      {selectedUser && (
        <div className="user-info">
          Chatting as: <strong>{selectedUser.firstname} {selectedUser.lastname}</strong> 
          ({selectedUser.role})
        </div>
      )}

      <main className="app-main">
        <HowTo />
        <ChatWindow messages={messages} />
      </main>

      <footer className="app-footer">
        <ChatInput
          ref={chatInputRef}
          onSendMessage={handleSendMessage}
          disabled={!selectedUserId}
          isLoading={isLoading}
        />
      </footer>

      {selectedUserId && (
        <DebugModal
          userId={selectedUserId}
          isOpen={isDebugOpen}
          onClose={() => setIsDebugOpen(false)}
          onConversationsDeleted={() => setMessages([])}
        />
      )}
    </div>
  );
}

export default App;
