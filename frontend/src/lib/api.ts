import type {
  User,
  UserProfile,
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  Session,
  SessionCreate,
  Message,
  ChatHistory,
  Attachment,
  Exercise,
  ExerciseGenerateRequest,
  ExerciseSubmitRequest,
  SessionListResponse,
  ExerciseListResponse,
} from "@/types";

// ═══════════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════════

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

// ═══════════════════════════════════════════════════════════════════════════════
// Token Management
// ═══════════════════════════════════════════════════════════════════════════════

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
  if (typeof window !== "undefined") {
    if (token) {
      localStorage.setItem("access_token", token);
    } else {
      localStorage.removeItem("access_token");
    }
  }
}

export function getAccessToken(): string | null {
  if (accessToken) return accessToken;
  if (typeof window !== "undefined") {
    accessToken = localStorage.getItem("access_token");
  }
  return accessToken;
}

export function clearTokens() {
  accessToken = null;
  if (typeof window !== "undefined") {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// Fetch Wrapper
// ═══════════════════════════════════════════════════════════════════════════════

interface FetchOptions extends RequestInit {
  requireAuth?: boolean;
}

async function apiFetch<T>(
  endpoint: string,
  options: FetchOptions = {}
): Promise<T> {
  const { requireAuth = true, ...fetchOptions } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers || {}),
  };

  if (requireAuth) {
    const token = getAccessToken();
    if (token) {
      (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) return {} as T;

  return JSON.parse(text);
}

// ═══════════════════════════════════════════════════════════════════════════════
// Auth API
// ═══════════════════════════════════════════════════════════════════════════════

export const auth = {
  async register(data: RegisterRequest): Promise<AuthTokens> {
    const tokens = await apiFetch<AuthTokens>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
      requireAuth: false,
    });
    setAccessToken(tokens.access_token);
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", tokens.refresh_token);
    }
    return tokens;
  },

  async login(data: LoginRequest): Promise<AuthTokens> {
    // OAuth2PasswordRequestForm expects form data with 'username' field
    const formData = new URLSearchParams();
    formData.append("username", data.email);
    formData.append("password", data.password);

    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    const tokens: AuthTokens = await response.json();
    setAccessToken(tokens.access_token);
    if (typeof window !== "undefined") {
      localStorage.setItem("refresh_token", tokens.refresh_token);
    }
    return tokens;
  },

  async logout(): Promise<void> {
    clearTokens();
  },

  async me(): Promise<User> {
    return apiFetch<User>("/auth/me");
  },

  async refresh(): Promise<AuthTokens> {
    const refreshToken = typeof window !== "undefined"
      ? localStorage.getItem("refresh_token")
      : null;

    const tokens = await apiFetch<AuthTokens>("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
      requireAuth: false,
    });
    setAccessToken(tokens.access_token);
    return tokens;
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Users API
// ═══════════════════════════════════════════════════════════════════════════════

export const users = {
  async getProfile(): Promise<UserProfile> {
    return apiFetch<UserProfile>("/users/profile");
  },

  async updateProfile(data: Partial<UserProfile>): Promise<UserProfile> {
    return apiFetch<UserProfile>("/users/profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Sessions API
// ═══════════════════════════════════════════════════════════════════════════════

export const sessions = {
  async list(): Promise<SessionListResponse> {
    return apiFetch<SessionListResponse>("/sessions");
  },

  async get(id: string): Promise<Session> {
    return apiFetch<Session>(`/sessions/${id}`);
  },

  async create(data: SessionCreate): Promise<Session> {
    return apiFetch<Session>("/sessions", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: Partial<SessionCreate>): Promise<Session> {
    return apiFetch<Session>(`/sessions/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  async delete(id: string): Promise<void> {
    await apiFetch<void>(`/sessions/${id}`, { method: "DELETE" });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Chat API
// ═══════════════════════════════════════════════════════════════════════════════

export const chat = {
  async getHistory(sessionId: string): Promise<ChatHistory> {
    return apiFetch<ChatHistory>(`/sessions/${sessionId}/chat`);
  },

  async sendMessage(sessionId: string, content: string): Promise<Message> {
    return apiFetch<Message>(`/sessions/${sessionId}/chat`, {
      method: "POST",
      body: JSON.stringify({ content }),
    });
  },

  async clearHistory(sessionId: string): Promise<void> {
    await apiFetch<void>(`/sessions/${sessionId}/chat`, { method: "DELETE" });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Attachments API
// ═══════════════════════════════════════════════════════════════════════════════

export const attachments = {
  async list(sessionId: string): Promise<Attachment[]> {
    return apiFetch<Attachment[]>(`/sessions/${sessionId}/attachments`);
  },

  async upload(sessionId: string, file: File): Promise<Attachment> {
    const formData = new FormData();
    formData.append("file", file);

    const token = getAccessToken();
    const response = await fetch(
      `${API_URL}/sessions/${sessionId}/attachments`,
      {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        body: formData,
      }
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Upload failed" }));
      throw new Error(error.detail);
    }

    return response.json();
  },

  async getStatus(sessionId: string, attachmentId: string): Promise<{
    id: string;
    is_processed: boolean;
    chunk_count: number;
    processing_error: string | null;
  }> {
    return apiFetch(`/sessions/${sessionId}/attachments/${attachmentId}/status`);
  },

  async delete(sessionId: string, attachmentId: string): Promise<void> {
    await apiFetch<void>(`/sessions/${sessionId}/attachments/${attachmentId}`, {
      method: "DELETE",
    });
  },

  getDownloadUrl(sessionId: string, attachmentId: string): string {
    return `${API_URL}/sessions/${sessionId}/attachments/${attachmentId}/download`;
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Exercises API
// ═══════════════════════════════════════════════════════════════════════════════

export const exercises = {
  async list(sessionId: string): Promise<ExerciseListResponse> {
    return apiFetch<ExerciseListResponse>(`/sessions/${sessionId}/exercises`);
  },

  async get(sessionId: string, exerciseId: string): Promise<Exercise> {
    return apiFetch<Exercise>(`/sessions/${sessionId}/exercises/${exerciseId}`);
  },

  async generate(
    sessionId: string,
    data: ExerciseGenerateRequest
  ): Promise<Exercise> {
    return apiFetch<Exercise>(`/sessions/${sessionId}/exercises/generate`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  async submit(
    sessionId: string,
    exerciseId: string,
    data: ExerciseSubmitRequest
  ): Promise<Exercise> {
    return apiFetch<Exercise>(
      `/sessions/${sessionId}/exercises/${exerciseId}/submit`,
      {
        method: "POST",
        body: JSON.stringify(data),
      }
    );
  },

  async getResults(sessionId: string, exerciseId: string): Promise<Exercise> {
    return apiFetch<Exercise>(
      `/sessions/${sessionId}/exercises/${exerciseId}/results`
    );
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// Default Export
// ═══════════════════════════════════════════════════════════════════════════════

const api = {
  auth,
  users,
  sessions,
  chat,
  attachments,
  exercises,
};

export default api;
