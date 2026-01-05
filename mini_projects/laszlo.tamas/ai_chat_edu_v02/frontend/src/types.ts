export interface Tenant {
  id: number;
  key: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  description?: string;
  system_prompt?: string;
  settings?: any;
}

export interface User {
  user_id: number;
  tenant_id?: number;
  firstname: string;
  lastname: string;
  nickname: string;
  email: string;
  role: string;
  is_active: boolean;
  default_lang?: string;
  system_prompt?: string;
  created_at: string;
}

export interface Message {
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  timestamp: string;
  sources?: {id: number; title: string}[];
  responseTime?: number; // milliseconds
  ragParams?: {
    top_k: number;
    min_score_threshold: number;
  };
  promptDetails?: {
    application?: string;
    tenant?: string | null;
    user?: string | null;
    user_context?: string;
    combined?: string;
    rag_context?: string;
    user_message?: string;
    mode?: string;
  };
}

export interface ChatRequest {
  user_id: number;
  tenant_id: number;
  session_id: string;
  message: string;
}

export interface ChatResponse {
  answer: string;
  sources?: {id: number; title: string}[];
  error?: string | null;
  rag_params?: {
    top_k: number;
    min_score_threshold: number;
  };
  prompt_details?: {
    application?: string;
    tenant?: string | null;
    user?: string | null;
    user_context?: string;
    combined?: string;
    rag_context?: string;
    user_message?: string;
    mode?: string;
  };
}

export interface MessageExchange {
  timestamp: string;
  user_message: string;
  assistant_message: string | null;
}

export interface Document {
  id: number;
  tenant_id: number;
  user_id: number | null;
  visibility: 'private' | 'tenant';
  source: string;
  title: string;
  created_at: string;
}

export interface LangGraphMessage {
  type: 'system' | 'human' | 'ai';
  content: string;
  timestamp?: string;
}

export interface LangGraphState {
  messages: LangGraphMessage[];
  user_context: {
    user_id: number;
    tenant_id: number;
    nickname: string;
    firstname: string;
    lastname: string;
    role: string;
    default_lang: string;
  };
  total_messages: number;
}

export interface DocumentChunk {
  chunk_id: number;
  document_id: number;
  content: string;
  metadata: Record<string, any>;
  similarity_score: number;
}

export interface RAGWorkflowState {
  query: string | null;
  user_context: Record<string, any>;
  system_prompt: string | null;
  combined_prompt: string | null;
  needs_rag: boolean;
  retrieved_chunks: DocumentChunk[];
  has_relevant_context: boolean;
  final_answer: string | null;
  sources: number[];
  error: string | null;
}

export interface DocumentProcessingState {
  filename: string | null;
  file_type: string | null;
  tenant_id: number | null;
  user_id: number | null;
  visibility: string | null;
  extracted_text: string | null;
  document_id: number | null;
  chunk_ids: number[];
  embedding_count: number;
  qdrant_point_ids: string[];
  status: string;
  error: string | null;
  processing_summary: Record<string, any>;
}

export interface SessionMemoryState {
  session_id: string | null;
  tenant_id: number | null;
  user_id: number | null;
  session_data: Record<string, any> | null;
  interactions: any[];
  interaction_count: number;
  needs_summary: boolean;
  summary_text: string | null;
  embedding_vector: number[] | null;
  qdrant_point_id: string | null;
  ltm_id: number | null;
  status: string;
  error: string | null;
  processing_summary: Record<string, any>;
}

export interface AllWorkflowStates {
  chat: LangGraphState;
  rag: RAGWorkflowState;
  document_processing: DocumentProcessingState;
  session_memory: SessionMemoryState;
}

export interface DebugInfo {
  user_data: User;
  last_exchanges: MessageExchange[];
  accessible_documents: Document[];
  workflow_states: AllWorkflowStates;
}
