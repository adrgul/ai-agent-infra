/**
 * Type definitions for the AI Agent application.
 */

export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface ChatRequest {
  user_id: string;
  message: string;
  session_id?: string;
}

export interface ToolUsed {
  name: string;
  arguments: Record<string, any>;
  success: boolean;
}

export interface MemorySnapshot {
  preferences: {
    language: string;
    default_city: string;
    [key: string]: any;
  };
  workflow_state: {
    flow: string | null;
    step: number;
    total_steps: number;
    data: Record<string, any>;
  };
  message_count: number;
}

export interface ChatResponse {
  final_answer: string;
  tools_used: ToolUsed[];
  memory_snapshot: MemorySnapshot;
  logs?: string[];
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  toolsUsed?: ToolUsed[];
}
