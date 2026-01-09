/**
 * ============================================================================
 * 🌐 API CLIENT - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Centralized API client for all backend communication.
 * Includes REST endpoints, WebSocket streaming, and file uploads.
 */

import type {
  ApiResponse,
  Session,
  CreateSessionResponse,
  QueryResult,
  DashboardData,
  DataProfile,
  ChartRecommendation,
  ExportOptions,
  ExportResult,
  UploadedFile,
} from '@/types';

// =============================================================================
// CONFIGURATION
// =============================================================================

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Default request options
const defaultHeaders: HeadersInit = {
  'Content-Type': 'application/json',
};

// =============================================================================
// ERROR HANDLING
// =============================================================================

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.message || errorData.detail || `HTTP ${response.status}`,
      errorData
    );
  }
  
  // Handle empty responses
  const text = await response.text();
  if (!text) return {} as T;
  
  try {
    return JSON.parse(text);
  } catch {
    return text as unknown as T;
  }
}

// =============================================================================
// REQUEST HELPERS
// =============================================================================

async function get<T>(endpoint: string, params?: Record<string, string>): Promise<T> {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  
  const response = await fetch(url.toString(), {
    method: 'GET',
    headers: defaultHeaders,
    credentials: 'include',
  });
  
  return handleResponse<T>(response);
}

async function post<T>(endpoint: string, data?: any): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: defaultHeaders,
    credentials: 'include',
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

async function put<T>(endpoint: string, data?: any): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'PUT',
    headers: defaultHeaders,
    credentials: 'include',
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

async function del<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'DELETE',
    headers: defaultHeaders,
    credentials: 'include',
  });
  
  return handleResponse<T>(response);
}

async function uploadFile<T>(
  endpoint: string,
  file: File,
  onProgress?: (progress: number) => void
): Promise<T> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);
    
    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        onProgress(progress);
      }
    });
    
    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          resolve(xhr.responseText as unknown as T);
        }
      } else {
        reject(new ApiError(xhr.status, xhr.statusText));
      }
    });
    
    xhr.addEventListener('error', () => {
      reject(new ApiError(0, 'Network error'));
    });
    
    xhr.open('POST', `${API_BASE_URL}${endpoint}`);
    xhr.withCredentials = true;
    xhr.send(formData);
  });
}

// =============================================================================
// SESSION API
// =============================================================================

export const sessionApi = {
  /**
   * Create a new analysis session
   */
  async create(userId?: string): Promise<CreateSessionResponse> {
    return post<CreateSessionResponse>('/api/sessions', { userId });
  },
  
  /**
   * Get session by ID
   */
  async get(sessionId: string): Promise<Session> {
    return get<Session>(`/api/sessions/${sessionId}`);
  },
  
  /**
   * List all sessions
   */
  async list(): Promise<Session[]> {
    return get<Session[]>('/api/sessions');
  },
  
  /**
   * Close a session
   */
  async close(sessionId: string): Promise<void> {
    return del(`/api/sessions/${sessionId}`);
  },
  
  /**
   * Upload a file to a session
   */
  async uploadFile(
    sessionId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<QueryResult> {
    return uploadFile<QueryResult>(
      `/api/sessions/${sessionId}/upload`,
      file,
      onProgress
    );
  },
  
  /**
   * Send a natural language query
   */
  async query(sessionId: string, query: string): Promise<QueryResult> {
    return post<QueryResult>(`/api/sessions/${sessionId}/query`, { query });
  },
  
  /**
   * Get data profile for session
   */
  async getProfile(sessionId: string): Promise<DataProfile> {
    return get<DataProfile>(`/api/sessions/${sessionId}/profile`);
  },
  
  /**
   * Get chart recommendations
   */
  async getChartRecommendations(
    sessionId: string,
    question?: string
  ): Promise<ChartRecommendation[]> {
    return post<ChartRecommendation[]>(
      `/api/sessions/${sessionId}/recommend-charts`,
      { question }
    );
  },
};

// =============================================================================
// DASHBOARD API
// =============================================================================

export const dashboardApi = {
  /**
   * Create a new dashboard
   */
  async create(
    sessionId: string,
    title: string,
    template?: string
  ): Promise<DashboardData> {
    return post<DashboardData>('/api/dashboards', {
      sessionId,
      title,
      template,
    });
  },
  
  /**
   * Get dashboard by ID
   */
  async get(dashboardId: string): Promise<DashboardData> {
    return get<DashboardData>(`/api/dashboards/${dashboardId}`);
  },
  
  /**
   * List all dashboards
   */
  async list(): Promise<DashboardData[]> {
    return get<DashboardData[]>('/api/dashboards');
  },
  
  /**
   * Update a dashboard
   */
  async update(
    dashboardId: string,
    updates: Partial<DashboardData>
  ): Promise<DashboardData> {
    return put<DashboardData>(`/api/dashboards/${dashboardId}`, updates);
  },
  
  /**
   * Delete a dashboard
   */
  async delete(dashboardId: string): Promise<void> {
    return del(`/api/dashboards/${dashboardId}`);
  },
  
  /**
   * Export a dashboard
   */
  async export(
    dashboardId: string,
    options: ExportOptions
  ): Promise<ExportResult> {
    return post<ExportResult>(`/api/dashboards/${dashboardId}/export`, options);
  },
};

// =============================================================================
// STREAMING API (WebSocket)
// =============================================================================

type StreamingCallback = (content: string) => void;
type CompleteCallback = (result: QueryResult) => void;
type ErrorCallback = (error: Error) => void;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string;
  private onStream: StreamingCallback;
  private onComplete: CompleteCallback;
  private onError: ErrorCallback;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  
  constructor(
    sessionId: string,
    onStream: StreamingCallback,
    onComplete: CompleteCallback,
    onError: ErrorCallback
  ) {
    this.sessionId = sessionId;
    this.onStream = onStream;
    this.onComplete = onComplete;
    this.onError = onError;
  }
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(`${WS_BASE_URL}/ws/chat/${this.sessionId}`);
        
        this.ws.onopen = () => {
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
              case 'stream':
                this.onStream(data.content);
                break;
              case 'complete':
                this.onComplete(data.result);
                break;
              case 'error':
                this.onError(new Error(data.message));
                break;
            }
          } catch (e) {
            // Raw text stream
            this.onStream(event.data);
          }
        };
        
        this.ws.onerror = (event) => {
          this.onError(new Error('WebSocket error'));
        };
        
        this.ws.onclose = (event) => {
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
          }
        };
      } catch (e) {
        reject(e);
      }
    });
  }
  
  send(query: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'query', content: query }));
    } else {
      this.onError(new Error('WebSocket not connected'));
    }
  }
  
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
  
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }
}

// =============================================================================
// EXPORT API
// =============================================================================

export const exportApi = {
  /**
   * Export chart to image
   */
  async chartToImage(chartId: string, format: 'png' | 'svg' = 'png'): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/export/chart/${chartId}`, {
      method: 'POST',
      headers: defaultHeaders,
      credentials: 'include',
      body: JSON.stringify({ format }),
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, 'Export failed');
    }
    
    return response.blob();
  },
  
  /**
   * Export data to CSV/Excel
   */
  async dataToFile(
    sessionId: string,
    format: 'csv' | 'xlsx' = 'csv'
  ): Promise<Blob> {
    const response = await fetch(
      `${API_BASE_URL}/api/export/data/${sessionId}?format=${format}`,
      {
        method: 'GET',
        credentials: 'include',
      }
    );
    
    if (!response.ok) {
      throw new ApiError(response.status, 'Export failed');
    }
    
    return response.blob();
  },
  
  /**
   * Download a blob as file
   */
  downloadBlob(blob: Blob, filename: string): void {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};

// =============================================================================
// HEALTH CHECK
// =============================================================================

export async function checkApiHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: defaultHeaders,
    });
    return response.ok;
  } catch {
    return false;
  }
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export const api = {
  session: sessionApi,
  dashboard: dashboardApi,
  export: exportApi,
  checkHealth: checkApiHealth,
  ChatWebSocket,
};

export default api;
