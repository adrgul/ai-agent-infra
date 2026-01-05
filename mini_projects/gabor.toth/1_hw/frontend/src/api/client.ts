import axios from "axios";
import { CityBriefingResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:3000/api";

console.log("📡 API Base URL:", API_BASE_URL);

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log("📤 API Request:", config.method?.toUpperCase(), config.url, config.params);
  return config;
});

// Add response interceptor for logging
apiClient.interceptors.response.use(
  (response) => {
    console.log("📥 API Response:", response.status, response.data);
    return response;
  },
  (error) => {
    console.error("❌ API Error:", error.response?.status, error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export const briefingAPI = {
  getBriefing: (params: {
    city: string;
    activity?: string;
  }) => apiClient.get<CityBriefingResponse>("/briefing", { params }),

  getHistory: (limit: number = 20) =>
    apiClient.get<CityBriefingResponse[]>("/history", {
      params: { limit },
    }),
};
