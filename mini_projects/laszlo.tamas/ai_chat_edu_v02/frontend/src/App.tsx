import { useState, useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { User, Message } from "./types";
import { fetchUsers, sendChatMessage, fetchSessionMessages } from "./api";
import { UserDropdown } from "./components/UserDropdown";
import { TenantDropdown } from "./components/TenantDropdown";
import { ChatWindow } from "./components/ChatWindow";
import { ChatInput, ChatInputRef } from "./components/ChatInput";
import { DebugModal } from "./components/DebugModal";
import { PromptInspector } from "./components/PromptInspector";
import { HowTo } from "./components/HowTo";
import { DocumentUpload } from "./components/DocumentUpload";
import { Sidebar, SidebarRef } from "./components/Sidebar";
import "./App.css";

function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedTenantId, setSelectedTenantId] = useState<number | null>(null);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDebugOpen, setIsDebugOpen] = useState(false);
  const [isPromptInspectorOpen, setIsPromptInspectorOpen] = useState(false);
  const [currentPromptDetails, setCurrentPromptDetails] = useState<any>(null);
  const [isHowToOpen, setIsHowToOpen] = useState(false);
  const [isDocumentUploadOpen, setIsDocumentUploadOpen] = useState(false);
  const chatInputRef = useRef<ChatInputRef>(null);
  const sidebarRef = useRef<SidebarRef>(null);

  // Load users when tenant changes
  useEffect(() => {
    if (selectedTenantId) {
      fetchUsers(selectedTenantId)
        .then((data) => {
          setUsers(data);
          
          // Try to restore last selected user for this tenant
          const savedUserIdKey = `lastUserId_tenant_${selectedTenantId}`;
          const savedUserId = localStorage.getItem(savedUserIdKey);
          
          if (savedUserId) {
            const savedUserIdNum = Number(savedUserId);
            const userExists = data.find(u => u.user_id === savedUserIdNum);
            if (userExists) {
              // Restore saved user for this tenant
              handleUserChange(savedUserIdNum);
              return;
            }
          }
          
          // If no saved user or user doesn't exist, auto-select first user
          if (data.length > 0) {
            handleUserChange(data[0].user_id);
          } else {
            // No users for this tenant
            setSelectedUserId(null);
            setMessages([]);
          }
        })
        .catch((err) => {
          console.error("Failed to load users:", err);
          setError("Failed to load users for selected tenant.");
          setUsers([]);
        });
    }
  }, [selectedTenantId]);

  // Handle user change
  const handleUserChange = async (userId: number) => {
    setSelectedUserId(userId);
    
    // Save this user selection for the current tenant
    if (selectedTenantId) {
      localStorage.setItem(`lastUserId_tenant_${selectedTenantId}`, userId.toString());
    }
    
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

    // Focus input after user change
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 0);
  };

  // Handle new chat creation
  const handleNewChat = () => {
    if (!selectedUserId) return;
    
    const newSessionId = uuidv4();
    localStorage.setItem(`activeSessionId_user_${selectedUserId}`, newSessionId);
    setActiveSessionId(newSessionId);
    setSessionId(newSessionId);
    setMessages([]);
    setError(null);
    
    // Focus input
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 0);
  };

  // Handle session selection
  const handleSessionSelect = async (selectedSessionId: string) => {
    if (!selectedUserId) return;
    
    localStorage.setItem(`activeSessionId_user_${selectedUserId}`, selectedSessionId);
    setActiveSessionId(selectedSessionId);
    setSessionId(selectedSessionId);
    setError(null);
    
    // Load messages for selected session
    try {
      const previousMessages = await fetchSessionMessages(selectedSessionId);
      setMessages(previousMessages);
    } catch (err) {
      console.error("Failed to load session messages:", err);
      setMessages([]);
      setError("Failed to load session history");
    }
  };

  // Handle session deletion
  const handleSessionDelete = (deletedSessionId: string) => {
    // If deleted session was active, clear messages
    if (deletedSessionId === activeSessionId) {
      setMessages([]);
      setActiveSessionId(null);
      setSessionId("");
    }
  };

  // Handle session rename (just update local state if needed)
  const handleSessionRename = (renamedSessionId: string, newTitle: string) => {
    // Could update UI if showing session title in header
    console.log(`Session ${renamedSessionId} renamed to: ${newTitle}`);
  };

  // Restore active session on user change
  useEffect(() => {
    if (selectedUserId) {
      const savedActiveSessionId = localStorage.getItem(`activeSessionId_user_${selectedUserId}`);
      if (savedActiveSessionId) {
        setActiveSessionId(savedActiveSessionId);
        setSessionId(savedActiveSessionId);
        // Load messages
        fetchSessionMessages(savedActiveSessionId)
          .then(setMessages)
          .catch(() => setMessages([]));
      } else {
        // Create new session
        handleNewChat();
      }
    }
  }, [selectedUserId]);

  // Handle sending a message
  const handleSendMessage = async (messageContent: string) => {
    if (!selectedUserId || !sessionId || !selectedTenantId) return;

    // Add user message to UI
    const userMessage: Message = {
      role: "user",
      content: messageContent,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    
    // Start timer
    const startTime = Date.now();

    try {
      const response = await sendChatMessage({
        user_id: selectedUserId,
        tenant_id: selectedTenantId,
        session_id: sessionId,
        message: messageContent,
      });
      
      // Calculate response time
      const endTime = Date.now();
      const responseTimeMs = endTime - startTime;

      // Add assistant message to UI
      const assistantMessage: Message = {
        role: "assistant",
        content: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources,
        responseTime: responseTimeMs,
        ragParams: response.rag_params,
        promptDetails: response.prompt_details,
      };
      setMessages((prev) => [...prev, assistantMessage]);
      
      // Store latest prompt details for inspector
      if (response.prompt_details) {
        setCurrentPromptDetails(response.prompt_details);
      }
      
      // Refresh sidebar to show updated session
      sidebarRef.current?.refreshSessions();
      
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
  const [appVersion, setAppVersion] = useState<string>("");

  // Fetch app version
  useEffect(() => {
    const apiUrl = import.meta.env.VITE_API_URL?.replace('/api', '') || 'http://localhost:18000';
    fetch(`${apiUrl}/api/version`)
      .then(res => res.json())
      .then(data => {
        setAppVersion(data.version);
        document.title = `AI Chat ${data.version}`; // Update browser tab title
      })
      .catch(() => {
        setAppVersion("0.2.0");
        document.title = "AI Chat 0.2.0"; // Fallback title
      });
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>{appVersion ? `AI Chat ${appVersion}` : "AI Chat"}</h1>
        <div className="header-controls">
          <TenantDropdown
            selectedTenantId={selectedTenantId}
            onTenantChange={setSelectedTenantId}
          />
          <UserDropdown
            users={users}
            selectedUserId={selectedUserId}
            onUserChange={handleUserChange}
          />
        </div>
      </header>

      {selectedUserId && (
        <>
          <button 
            className="howto-button" 
            onClick={() => setIsHowToOpen(!isHowToOpen)}
            title="How To Test guide"
          >
            📖 How To Test
          </button>
          <button 
            className="debug-button" 
            onClick={() => setIsDebugOpen(!isDebugOpen)}
            title="Debug információk"
          >
            🐛 Debug
          </button>
          <button 
            className="prompt-inspector-button" 
            onClick={() => setIsPromptInspectorOpen(!isPromptInspectorOpen)}
            title="LLM Prompt Inspector"
            disabled={!currentPromptDetails}
          >
            🔍 Prompt
          </button>
        </>
      )}

      {error && <div className="error-banner">{error}</div>}

      {selectedUser && (
        <div className="user-info">
          Chatting as: <strong>{selectedUser.firstname} {selectedUser.lastname}</strong> 
          ({selectedUser.role})
        </div>
      )}

      <div className="app-main">
        <div className="page-wrapper">
          {selectedUserId && isHowToOpen && (
            <aside className="sidebar-left">
              <HowTo />
            </aside>
          )}
          
          <main className="chat-section">
            {/* Sidebar with session list */}
            {selectedUserId && (
              <Sidebar
                ref={sidebarRef}
                userId={selectedUserId}
                activeSessionId={activeSessionId}
                onSessionSelect={handleSessionSelect}
                onNewChat={handleNewChat}
                onSessionDelete={handleSessionDelete}
                onSessionRename={handleSessionRename}
              />
            )}

            <div className="chat-container">
              <ChatWindow messages={messages} isLoading={isLoading} />
              
              <footer className="app-footer">
                <ChatInput
                  ref={chatInputRef}
                  onSendMessage={handleSendMessage}
                  disabled={!selectedUserId}
                  isLoading={isLoading}
                  hasDocumentUpload={!!selectedUserId && !!selectedTenantId}
                  onDocumentUploadClick={() => setIsDocumentUploadOpen(true)}
                />
              </footer>
            </div>
          </main>

          {selectedUserId && selectedTenantId && isDebugOpen && (
            <aside className="sidebar-right">
              <DebugModal
                userId={selectedUserId}
                sessionId={activeSessionId}
                isOpen={isDebugOpen}
                onClose={() => setIsDebugOpen(false)}
                onConversationsDeleted={() => setMessages([])}
              />
            </aside>
          )}
        </div>
      </div>

      {/* Prompt Inspector Modal */}
      <PromptInspector
        promptDetails={currentPromptDetails}
        isOpen={isPromptInspectorOpen}
        onClose={() => setIsPromptInspectorOpen(false)}
      />

      {/* Document Upload Modal */}
      {selectedUserId && selectedTenantId && (
        <DocumentUpload
          tenantId={selectedTenantId}
          userId={selectedUserId}
          compact={true}
          isOpen={isDocumentUploadOpen}
          onClose={() => setIsDocumentUploadOpen(false)}
        />
      )}
    </div>
  );
}

export default App;
