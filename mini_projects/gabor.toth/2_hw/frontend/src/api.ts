import axios from 'axios';

const API_BASE = '/api';

export interface Message {
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

export interface UploadResponse {
  upload_id: string;
  filename: string;
  category: string;
  size: number;
  created_at: string;
}

export interface ChatResponse {
  final_answer: string;
  fallback_search?: boolean;
  tools_used: { name: string; description: string }[];
  memory_snapshot: {
    routed_category?: string | null;
    available_categories: string[];
  };
  rag_debug?: {
    retrieved: Array<{
      chunk_id: string;
      distance: number;
      snippet: string;
      metadata: Record<string, any>;
      content?: string;
      source_file?: string;
      section_title?: string;
    }>;
  };
}

// Chat API
export const chatAPI = {
  async sendMessage(
    userId: string,
    sessionId: string,
    message: string
  ): Promise<ChatResponse> {
    const formData = new FormData();
    formData.append('user_id', userId);
    formData.append('session_id', sessionId);
    formData.append('message', message);

    const response = await axios.post(`${API_BASE}/chat`, formData);
    return response.data;
  },

  async getSession(sessionId: string): Promise<Message[]> {
    const response = await axios.get(`${API_BASE}/session/${sessionId}`);
    return response.data;
  },
};

// Upload API
export const uploadAPI = {
  async uploadFile(
    category: string,
    file: File,
    chunkSizeTokens: number = 900,
    overlapTokens: number = 150,
    embeddingBatchSize: number = 100
  ): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);
    formData.append('chunk_size_tokens', chunkSizeTokens.toString());
    formData.append('overlap_tokens', overlapTokens.toString());
    formData.append('embedding_batch_size', embeddingBatchSize.toString());

    const response = await axios.post(`${API_BASE}/files/upload`, formData);
    return response.data;
  },

  async deleteFile(
    category: string,
    uploadId: string,
    filename: string
  ): Promise<void> {
    const params = new URLSearchParams({
      category,
      filename,
    });

    await axios.delete(`${API_BASE}/files/${uploadId}?${params}`);
  },

  async listFiles(category: string): Promise<UploadResponse[]> {
    const response = await axios.get(`${API_BASE}/documents?category=${encodeURIComponent(category)}`);
    return response.data;
  },

  async saveDescription(
    category: string,
    description: string
  ): Promise<void> {
    const formData = new FormData();
    formData.append('category', category);
    formData.append('description', description);

    await axios.post(`${API_BASE}/desc-save`, formData);
  },

  async getDescription(
    category: string
  ): Promise<string | null> {
    try {
      const response = await axios.get(
        `${API_BASE}/desc-get?category=${encodeURIComponent(category)}`
      );
      return response.data.description || null;
    } catch {
      return null;
    }
  },

  async matchCategory(question: string): Promise<{
    category: string | null;
    confidence: number;
  }> {
    const formData = new FormData();
    formData.append('question', question);

    const response = await axios.post(`${API_BASE}/cat-match`, formData);
    return response.data;
  },
};

// Categories API
export const categoriesAPI = {
  async getCategories(): Promise<string[]> {
    const response = await axios.get(`${API_BASE}/categories`);
    return response.data;
  },

  async createCategory(category: string): Promise<void> {
    const formData = new FormData();
    formData.append('category', category);
    await axios.post(`${API_BASE}/categories`, formData);
  },

  async deleteCategory(category: string): Promise<void> {
    await axios.delete(`${API_BASE}/categories`, {
      params: { category }
    });
  },
};

// Profile API
export const profileAPI = {
  async getProfile(userId: string) {
    const response = await axios.get(`${API_BASE}/profile/${userId}`);
    return response.data;
  },

  async updateProfile(userId: string, profile: Record<string, any>) {
    const response = await axios.put(`${API_BASE}/profile/${userId}`, profile);
    return response.data;
  },
};

// Health check
export const healthAPI = {
  async check(): Promise<boolean> {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      return response.status === 200;
    } catch {
      return false;
    }
  },
};
