import {
  User,
  Document,
  DocumentPreview,
  Conversation,
  Message,
  ResearchReport,
  EvaluationRun,
  DashboardStats,
  UsageSummary,
} from '../types';

const API_BASE = '/api';

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('cortex_access_token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  private async handleResponse<T>(res: Response): Promise<T> {
    if (res.status === 401) {
      // Clear token on authentication failure
      localStorage.removeItem('cortex_access_token');
      localStorage.removeItem('cortex_refresh_token');
    }
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errorData.detail || 'Request failed');
    }
    if (res.status === 204) {
      return {} as T;
    }
    return res.json();
  }

  // Auth Endpoints
  async register(data: { email: string; password: string; full_name?: string }): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return this.handleResponse<User>(res);
  }

  async login(data: { email: string; password: string }): Promise<{ access_token: string; refresh_token: string }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const tokens = await this.handleResponse<{ access_token: string; refresh_token: string }>(res);
    localStorage.setItem('cortex_access_token', tokens.access_token);
    localStorage.setItem('cortex_refresh_token', tokens.refresh_token);
    return tokens;
  }

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<User>(res);
  }

  async logout(): Promise<void> {
    await fetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
      headers: this.getHeaders(),
    });
    localStorage.removeItem('cortex_access_token');
    localStorage.removeItem('cortex_refresh_token');
  }

  // Documents Endpoints
  async uploadDocument(file: File): Promise<Document> {
    const token = localStorage.getItem('cortex_access_token');
    const formData = new FormData();
    formData.append('file', file);

    const headers: HeadersInit = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers,
      body: formData,
    });
    return this.handleResponse<Document>(res);
  }

  async importUrl(url: string, title?: string): Promise<Document> {
    const res = await fetch(`${API_BASE}/documents/import-url`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ url, title }),
    });
    return this.handleResponse<Document>(res);
  }

  async listDocuments(filter?: { file_type?: string; status?: string; search?: string }): Promise<Document[]> {
    const params = new URLSearchParams();
    if (filter?.file_type) params.append('file_type', filter.file_type);
    if (filter?.status) params.append('status', filter.status);
    if (filter?.search) params.append('search', filter.search);

    const res = await fetch(`${API_BASE}/documents?${params.toString()}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<Document[]>(res);
  }

  async getDocument(id: string): Promise<Document> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<Document>(res);
  }

  async deleteDocument(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<void>(res);
  }

  async getDocumentPreview(id: string): Promise<DocumentPreview> {
    const res = await fetch(`${API_BASE}/documents/${id}/preview`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<DocumentPreview>(res);
  }

  // Search
  async search(query: string, mode: string = 'hybrid', top_k: number = 5, document_ids?: string[]) {
    const res = await fetch(`${API_BASE}/search`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ query, mode, top_k, document_ids }),
    });
    return this.handleResponse<any>(res);
  }

  // Conversations & Chat
  async listConversations(): Promise<Conversation[]> {
    const res = await fetch(`${API_BASE}/conversations`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<Conversation[]>(res);
  }

  async getConversation(id: string): Promise<Conversation> {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<Conversation>(res);
  }

  async deleteConversation(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/conversations/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<void>(res);
  }

  async sendMessage(data: {
    conversation_id?: string;
    message: string;
    mode?: string;
    document_ids?: string[];
  }): Promise<Message> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<Message>(res);
  }

  // Reports
  async generateReport(data: {
    research_question: string;
    title?: string;
    focus_areas?: string[];
    document_ids?: string[];
  }): Promise<ResearchReport> {
    const res = await fetch(`${API_BASE}/reports/generate`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<ResearchReport>(res);
  }

  async listReports(): Promise<ResearchReport[]> {
    const res = await fetch(`${API_BASE}/reports`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<ResearchReport[]>(res);
  }

  async getReport(id: string): Promise<ResearchReport> {
    const res = await fetch(`${API_BASE}/reports/${id}`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<ResearchReport>(res);
  }

  async deleteReport(id: string): Promise<void> {
    const res = await fetch(`${API_BASE}/reports/${id}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<void>(res);
  }

  async exportReportMarkdown(id: string): Promise<string> {
    const res = await fetch(`${API_BASE}/reports/${id}/export`, {
      headers: this.getHeaders(),
    });
    return res.text();
  }

  // Evaluations
  async listEvaluationRuns(): Promise<EvaluationRun[]> {
    const res = await fetch(`${API_BASE}/evaluations`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<EvaluationRun[]>(res);
  }

  async runEvaluation(top_k: number = 3, retrieval_mode: string = 'hybrid'): Promise<EvaluationRun> {
    const res = await fetch(`${API_BASE}/evaluations/run`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ top_k, retrieval_mode }),
    });
    return this.handleResponse<EvaluationRun>(res);
  }

  // Analytics & Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const res = await fetch(`${API_BASE}/analytics/dashboard`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<DashboardStats>(res);
  }

  async getUsageSummary(): Promise<UsageSummary> {
    const res = await fetch(`${API_BASE}/analytics/usage`, {
      headers: this.getHeaders(),
    });
    return this.handleResponse<UsageSummary>(res);
  }
}

export const api = new ApiClient();
