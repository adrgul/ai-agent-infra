import type { BriefingResponse, HistoryEntry, UserProfile } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(
      error.detail || `HTTP ${response.status}: ${response.statusText}`,
      response.status,
      error.detail
    );
  }
  return response.json();
}

export async function getBriefing(
  city: string,
  date?: string,
  language?: string
): Promise<BriefingResponse> {
  const params = new URLSearchParams({ city });
  if (date) {
    params.append('date', date);
  }
  if (language) {
    params.append('language', language);
  }

  const response = await fetch(`${API_BASE}/api/briefing?${params}`);
  return handleResponse(response);
}

export async function getHistory(): Promise<HistoryEntry[]> {
  const response = await fetch(`${API_BASE}/api/history`);
  return handleResponse(response);
}

export async function getProfile(): Promise<UserProfile | null> {
  const response = await fetch(`${API_BASE}/api/profile`);
  return handleResponse(response);
}

export async function updateProfile(profile: UserProfile): Promise<UserProfile> {
  const response = await fetch(`${API_BASE}/api/profile`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(profile),
  });
  return handleResponse(response);
}
