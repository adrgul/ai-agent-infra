import { User, ChatRequest, ChatResponse, Message, DebugInfo, Tenant } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_URL;

// Runtime dev mode status (fetched from backend system.ini)
let cachedDevMode: boolean | null = null;

/**
 * Fetch dev mode status from backend (system.ini [development] DEV_MODE).
 * Cached after first call to avoid repeated requests.
 */
export async function getDevMode(): Promise<boolean> {
  if (cachedDevMode !== null) {
    return cachedDevMode;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/config/dev-mode`);
    if (!response.ok) {
      console.warn('Failed to fetch dev-mode, defaulting to false');
      cachedDevMode = false;
      return false;
    }
    const data = await response.json();
    cachedDevMode = data.dev_mode as boolean;
    console.log(`🔧 Dev mode (from system.ini): ${cachedDevMode}`);
    return cachedDevMode;
  } catch (error) {
    console.warn('Error fetching dev-mode:', error);
    cachedDevMode = false;
    return false;
  }
}

/**
 * Get default fetch headers with optional cache control for dev mode.
 * Dev mode is fetched from backend at runtime (system.ini).
 */
async function getDefaultHeaders(): Promise<HeadersInit> {
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  
  // Disable cache in dev mode (fetched from backend)
  const devMode = await getDevMode();
  if (devMode) {
    headers["Cache-Control"] = "no-cache, no-store, must-revalidate";
    headers["Pragma"] = "no-cache";
    headers["Expires"] = "0";
  }
  
  return headers;
}

export async function fetchTenants(activeOnly: boolean = true): Promise<Tenant[]> {
  const response = await fetch(`${API_BASE_URL}/tenants?active_only=${activeOnly}`, {
    headers: await getDefaultHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch tenants");
  }
  return response.json();
}

export async function fetchUsers(tenantId?: number): Promise<User[]> {
  const url = tenantId 
    ? `${API_BASE_URL}/users?tenant_id=${tenantId}`
    : `${API_BASE_URL}/users`;
  const response = await fetch(url, {
    headers: await getDefaultHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch users");
  }
  return response.json();
}

export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE_URL}/chat/rag`, {
    method: "POST",
    headers: await getDefaultHeaders(),
    body: JSON.stringify({
      user_id: request.user_id,
      tenant_id: request.tenant_id,
      session_id: request.session_id,
      query: request.message
    }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to send message");
  }
  
  return response.json();
}

export async function fetchSessionMessages(sessionId: string): Promise<Message[]> {
  const response = await fetch(`${API_BASE_URL}/chat/${sessionId}/messages`, {
    headers: await getDefaultHeaders(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch session messages");
  }
  const data = await response.json();
  return data.map((msg: any) => ({
    role: msg.role,
    content: msg.content,
    timestamp: msg.created_at,
    sources: msg.metadata?.sources || [],
    ragParams: msg.metadata?.rag_params || null,
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

export async function resetPostgres(): Promise<{ status: string; documents_deleted: number; chunks_deleted: number }> {
  const response = await fetch(`${API_BASE_URL}/debug/reset/postgres`, {
    method: "POST",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to reset PostgreSQL");
  }
  return response.json();
}

export async function resetQdrant(): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/debug/reset/qdrant`, {
    method: "POST",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to reset Qdrant");
  }
  return response.json();
}

export async function resetCache(): Promise<{ memory_cleared: boolean; db_cleared: number; error?: string }> {
  const response = await fetch(`${API_BASE_URL}/admin/cache/clear`, {
    method: "POST",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to reset cache");
  }
  return response.json();
}

export async function updateUser(userId: number, updates: Partial<User>): Promise<{ success: boolean; user: User }> {
  const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update user");
  }
  return response.json();
}

export async function updateTenant(tenantId: number, updates: Partial<Tenant>): Promise<{ success: boolean; tenant: Tenant }> {
  const response = await fetch(`${API_BASE_URL}/tenants/${tenantId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(updates),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update tenant");
  }
  return response.json();
}

// ============================================================================
// P0.17 - Cache Control API
// ============================================================================

export interface CacheStats {
  memory_cache: {
    enabled: boolean;
    size: number;
    keys: string[];
    ttl_seconds: number;
    debug_mode: boolean;
  };
  db_cache: {
    enabled: boolean;
    cached_users: number;
    total_entries: number;
    error?: string;
  };
  config: {
    memory_enabled: boolean;
    db_enabled: boolean;
    browser_enabled: boolean;
    llm_enabled: boolean;
  };
  timestamp: string;
}

export async function getCacheStats(): Promise<CacheStats> {
  const response = await fetch(`${API_BASE_URL}/admin/cache/stats`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to get cache stats");
  }
  return response.json();
}

export async function clearAllCaches(): Promise<{ memory_cleared: boolean; db_cleared: number }> {
  const response = await fetch(`${API_BASE_URL}/admin/cache/clear`, {
    method: "POST",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to clear caches");
  }
  return response.json();
}

export async function invalidateUserCache(userId: number): Promise<{ user_id: number; memory_cleared: number; db_cleared: number }> {
  const response = await fetch(`${API_BASE_URL}/admin/cache/user/${userId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to invalidate user cache");
  }
  return response.json();
}

export async function invalidateTenantCache(tenantId: number): Promise<{ tenant_id: number; users_affected: number; memory_cleared: number; db_cleared: number }> {
  const response = await fetch(`${API_BASE_URL}/admin/cache/tenant/${tenantId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to invalidate tenant cache");
  }
  return response.json();
}
