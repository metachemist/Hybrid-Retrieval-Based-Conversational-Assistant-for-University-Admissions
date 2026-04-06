/**
 * API Client for the Admission Chatbot Backend
 */

// In production (Vercel experimentalServices), backend is proxied at /_/backend
// For local dev, set NEXT_PUBLIC_API_URL=http://localhost:8000 in frontend/.env.local
const API_URL = process.env.NEXT_PUBLIC_API_URL || '/_/backend'

export interface ChatRequest {
  query: string
  top_k?: number
  use_hybrid?: boolean
  stream?: boolean
}

export interface ChatResponse {
  response: string
  citations: Citation[]
  latency_ms: number
  llm_provider: string
  cache_hit: boolean
  language: string
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
      const error = await response.text()
      throw new Error(`API Error: ${response.status} - ${error}`)
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

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.request<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    })
  }

  async getSuggestions(limit: number = 5): Promise<{ suggestions: string[] }> {
    return this.request<{ suggestions: string[] }>(`/api/chat/suggestions?limit=${limit}`)
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
      const error = await response.text()
      throw new Error(`Upload Error: ${response.status} - ${error}`)
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
