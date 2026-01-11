import React, { useEffect, useMemo, useState } from "react";
import ChatPanel, { ChatMessage } from "./components/ChatPanel";
import DebugSidebar, { DebugInfo } from "./components/DebugSidebar";
import AdminPanel from "./components/AdminPanel";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const generateId = (prefix: string) =>
  `${prefix}-${Math.random().toString(36).slice(2, 10)}`;

const App: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<DebugInfo>();

  const userId = useMemo(() => {
    const cached = localStorage.getItem("kr-user");
    if (cached) return cached;
    const newId = generateId("user");
    localStorage.setItem("kr-user", newId);
    return newId;
  }, []);

  const [sessionId, setSessionId] = useState(() => {
    const cached = localStorage.getItem("kr-session");
    if (cached) return cached;
    const newId = generateId("session");
    localStorage.setItem("kr-session", newId);
    return newId;
  });

  useEffect(() => {
    if (!localStorage.getItem("kr-session")) {
      localStorage.setItem("kr-session", sessionId);
    }
  }, [sessionId]);

  const submit = async () => {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: userId,
          session_id: sessionId,
          message: input,
          metadata: { client: "web" },
        }),
      });

      if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
      }

      const data = await response.json();
      const mappedMessages: ChatMessage[] = (data.history || []).map(
        (item: any) => ({
          role: item.role,
          content: item.content,
          timestamp: item.timestamp,
        })
      );
      setMessages(mappedMessages);
      setDebugInfo(data.debug);
      setSessionId(data.session_id);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error instanceof Error
              ? error.message
              : "Unexpected error contacting the API.",
        },
      ]);
    } finally {
      setInput("");
      setLoading(false);
    }
  };

  return (
    <div className="uk-container uk-container-expand uk-padding chat-container">
      <div className="uk-grid-large uk-child-width-1-3@s" data-uk-grid>
        <div className="uk-width-expand@m">
          <ChatPanel
            messages={messages}
          input={input}
          loading={loading}
          onInputChange={setInput}
          onSend={submit}
        />
      </div>
        <div className="uk-width-1-3@m">
          <DebugSidebar debug={debugInfo} />
          <div className="uk-margin-top">
            <h4 className="uk-text-bold">Admin</h4>
            <AdminPanel />
          </div>
        </div>
      </div>
    </div>
  );
};

export default App;
