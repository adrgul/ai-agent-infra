import { User, ChatRequest, ChatResponse, Message, DebugInfo } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

export async function fetchUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE_URL}/users`);
  if (!response.ok) {
    throw new Error("Failed to fetch users");
  }
  return response.json();
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to send message");
  }
  
  return response.json();
}

export async function fetchSessionMessages(sessionId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/chat/${sessionId}/messages`);
  if (!response.ok) {
    throw new Error("Failed to fetch session messages");
  }
  const data = await response.json();
  return data.map((msg: any) => ({
    role: msg.role,
    content: msg.content,
    timestamp: msg.created_at,
  }));
}

export async function fetchDebugInfo(userId: number): Promise<DebugInfo> {
  const response = await fetch(`${API_BASE_URL}/debug/${userId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch debug information");
  }
  return response.json();
}

export async function deleteUserConversations(userId: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/debug/${userId}/conversations`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete conversation history");
  }
}
