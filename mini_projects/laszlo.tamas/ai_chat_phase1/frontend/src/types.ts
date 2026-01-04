export interface User {
  user_id: number;
  firstname: string;
  lastname: string;
  nickname: string;
  email: string;
  role: string;
  is_active: boolean;
  default_lang?: string;
  created_at: string;
}

export interface Message {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  user_id: number;
  session_id: string;
  message: string;
}

export interface ChatResponse {
  answer: string;
}

export interface MessageExchange {
  timestamp: string;
  user_message: string;
  assistant_message: string | null;
}

export interface DebugInfo {
  user_data: User;
  ai_summary: string;
  last_exchanges: MessageExchange[];
}
