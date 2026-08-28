/**
 * API Client for the Admission Chatbot Backend
 */

// Backend runs on Render. Set NEXT_PUBLIC_API_URL to the Render backend URL
// in the Vercel project settings. For local dev, set it in frontend/.env.local
// (see .env.local.example).
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Thrown by ApiClient.request() with the backend's actual error message
// (FastAPI's {"detail": "..."}) and status code, so callers can branch on
// `status` reliably instead of substring-matching the raw response text.
export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export interface ChatRequest {
  query: string
  top_k?: number
  use_hybrid?: boolean
}

export interface Citation {
  index: number
  document_title: string
  section_header: string
  page_start: number
  page_end: number
  content_preview: string
}

export interface DocumentInfo {
  id: string
  title: string
  year: number | null
  chunk_count: number
  ingested_at: string
}

export interface HealthStatus {
  status: string
  version: string
  database: string
  llm_provider: string
  documents_count: number
  chunks_count: number
}

export interface AuthResponse {
  access_token: string
  token_type: string
  role: string
}

export interface UserProfile {
  id: string
  email: string
  role: string
}

export interface AnalyticsOverview {
  days: number
  total_queries: number
  unique_users: number
  avg_latency_ms: number
  cache_hit_rate_pct: number
  success_rate_pct: number
}

export interface QueryVolumePoint {
  date: string
  count: number
}

export interface LanguageStat {
  language: string
  count: number
}

export interface TopicStat {
  topic: string
  count: number
}

export interface PerformanceStats {
  days: number
  total_queries: number
  avg_latency_ms: number
  p95_latency_ms: number
  cache_hit_rate_pct: number
  error_rate_pct: number
}

export interface TopQuery {
  query: string
  count: number
}

export interface AdminUser {
  id: string
  email: string
  role: string
  created_at: string
}

class ApiClient {
  private baseUrl: string
  private token: string | null = null

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl
  }

  setToken(token: string) {
    this.token = token
  }

  clearToken() {
    this.token = null
  }

  private authHeaders(): Record<string, string> {
    return this.token ? { Authorization: `Bearer ${this.token}` } : {}
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...this.authHeaders(),
        ...options?.headers,
      },
      ...options,
    })

    if (!response.ok) {
      let message = response.statusText || `Request failed (${response.status})`
      try {
        const body = await response.json()
        if (body?.detail) {
          message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
        }
      } catch {
        // Response wasn't JSON - keep the fallback message.
      }
      throw new ApiError(response.status, message)
    }

    return response.json()
  }

  // -------------------------------------------------------------------------
  // Auth
  // -------------------------------------------------------------------------

  async login(email: string, password: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
  }

  async register(email: string, password: string, adminKey?: string): Promise<AuthResponse> {
    return this.request<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, admin_key: adminKey || undefined }),
    })
  }

  async getMe(): Promise<UserProfile> {
    return this.request<UserProfile>('/api/auth/me')
  }

  async forgotPassword(email: string): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/auth/forgot-password', {
      method: 'POST',
      body: JSON.stringify({ email }),
    })
  }

  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    return this.request<{ message: string }>('/api/auth/reset-password', {
      method: 'POST',
      body: JSON.stringify({ token, new_password: newPassword }),
    })
  }

  // -------------------------------------------------------------------------
  // Chat
  // -------------------------------------------------------------------------

  /**
   * Streaming chat over Server-Sent Events. Calls the handlers as events
   * arrive; resolves when the stream ends. Each SSE `data:` line is a JSON
   * object with a `type` of "meta" | "token" | "done" | "error".
   */
  async chatStream(
    request: ChatRequest,
    handlers: {
      onMeta?: (m: { language: string; citations: Citation[] }) => void
      onToken?: (text: string) => void
      onDone?: (d: { latency_ms: number; llm_provider: string; cache_hit?: boolean }) => void
      onError?: (message: string) => void
    },
    signal?: AbortSignal,
  ): Promise<void> {
    const response = await fetch(`${this.baseUrl}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...this.authHeaders() },
      body: JSON.stringify(request),
      signal,
    })

    if (!response.ok || !response.body) {
      let message = response.statusText || `Request failed (${response.status})`
      try {
        const body = await response.json()
        if (body?.detail) {
          message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
        }
      } catch {
        // not JSON — keep fallback
      }
      throw new ApiError(response.status, message)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const dispatch = (raw: string) => {
      const line = raw.trim()
      if (!line.startsWith('data:')) return
      let evt: any
      try {
        evt = JSON.parse(line.slice(5).trim())
      } catch {
        return
      }
      if (evt.type === 'meta') handlers.onMeta?.({ language: evt.language, citations: evt.citations ?? [] })
      else if (evt.type === 'token') handlers.onToken?.(evt.text ?? '')
      else if (evt.type === 'done')
        handlers.onDone?.({
          latency_ms: evt.latency_ms,
          llm_provider: evt.llm_provider,
          cache_hit: evt.cache_hit,
        })
      else if (evt.type === 'error') handlers.onError?.(evt.message ?? 'The response could not be completed.')
    }

    // SSE frames are separated by a blank line.
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let sep: number
      while ((sep = buffer.indexOf('\n\n')) !== -1) {
        dispatch(buffer.slice(0, sep))
        buffer = buffer.slice(sep + 2)
      }
    }
    if (buffer.trim()) dispatch(buffer)
  }

  // -------------------------------------------------------------------------
  // Documents
  // -------------------------------------------------------------------------

  async listDocuments(skip: number = 0, limit: number = 50): Promise<DocumentInfo[]> {
    return this.request<DocumentInfo[]>(`/api/documents?skip=${skip}&limit=${limit}`)
  }

  async getDocument(documentId: string): Promise<DocumentInfo> {
    return this.request<DocumentInfo>(`/api/documents/${documentId}`)
  }

  async uploadDocument(
    file: File,
    title?: string,
    year?: number,
  ): Promise<{ document_id: string; title: string; chunks_created: number; status: string }> {
    const formData = new FormData()
    formData.append('file', file)
    if (title) formData.append('title', title)
    if (year) formData.append('year', year.toString())

    const response = await fetch(`${this.baseUrl}/api/documents/upload`, {
      method: 'POST',
      headers: this.authHeaders(),
      body: formData,
    })

    if (!response.ok) {
      let message = response.statusText || `Upload failed (${response.status})`
      try {
        const body = await response.json()
        if (body?.detail) {
          message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
        }
      } catch {
        // Response wasn't JSON - keep the fallback message.
      }
      throw new ApiError(response.status, message)
    }

    return response.json()
  }

  async deleteDocument(documentId: string): Promise<{ status: string; document_id: string }> {
    return this.request(`/api/documents/${documentId}`, { method: 'DELETE' })
  }

  async reindexDocument(documentId: string): Promise<{ status: string; chunks_reindexed: number }> {
    return this.request(`/api/documents/${documentId}/reindex`, { method: 'POST' })
  }

  // -------------------------------------------------------------------------
  // Admin analytics
  // -------------------------------------------------------------------------

  async getAnalyticsOverview(days = 30): Promise<AnalyticsOverview> {
    return this.request<AnalyticsOverview>(`/api/admin/analytics/overview?days=${days}`)
  }

  async getQueryVolume(days = 30): Promise<QueryVolumePoint[]> {
    return this.request<QueryVolumePoint[]>(`/api/admin/analytics/queries?days=${days}`)
  }

  async getLanguageStats(days = 30): Promise<LanguageStat[]> {
    return this.request<LanguageStat[]>(`/api/admin/analytics/languages?days=${days}`)
  }

  async getTopicStats(days = 30): Promise<TopicStat[]> {
    return this.request<TopicStat[]>(`/api/admin/analytics/topics?days=${days}`)
  }

  async getPerformanceStats(days = 30): Promise<PerformanceStats> {
    return this.request<PerformanceStats>(`/api/admin/analytics/performance?days=${days}`)
  }

  async getTopQueries(days = 30, limit = 10): Promise<TopQuery[]> {
    return this.request<TopQuery[]>(`/api/admin/analytics/top-queries?days=${days}&limit=${limit}`)
  }

  async getUsers(): Promise<AdminUser[]> {
    return this.request<AdminUser[]>('/api/admin/users')
  }

  // -------------------------------------------------------------------------
  // Health
  // -------------------------------------------------------------------------

  async health(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/api/health')
  }
}

// Export singleton instance
export const api = new ApiClient()
