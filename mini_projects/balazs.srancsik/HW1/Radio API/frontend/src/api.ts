/**
 * API client for backend communication.
 */
import axios from 'axios';
import { ChatRequest, ChatResponse } from './types';

const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await apiClient.post<ChatResponse>('/chat', request);
    return response.data;
  },

  async getSession(sessionId: string) {
    const response = await apiClient.get(`/session/${sessionId}`);
    return response.data;
  },

  async getProfile(userId: string) {
    const response = await apiClient.get(`/profile/${userId}`);
    return response.data;
  },

  async updateProfile(userId: string, updates: any) {
    const response = await apiClient.put(`/profile/${userId}`, updates);
    return response.data;
  },

  async searchHistory(query: string) {
    const response = await apiClient.get('/history/search', {
      params: { q: query },
    });
    return response.data;
  },
};
