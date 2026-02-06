/**
 * ============================================================================
 * 🌐 API CLIENT - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Centralized API client for all backend communication.
 * FIXED: Matches the actual backend endpoints from main_production_with_rag.py
 * 
 * Backend Endpoints:
 * - POST /api/chat - Send chat message (RAG)
 * - WS /ws/chat/stream - WebSocket streaming chat
 * - GET /api/documents/list - List documents
 * - POST /api/documents/upload - Upload document
 * - GET /api/analytics/summary - Analytics data
 * - GET /api/conversations - Get conversations
 * - GET /health - Health check
 */

// =============================================================================
// CONFIGURATION
// =============================================================================

// Get API URL from environment or use default
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Debug mode - enable verbose logging
const DEBUG = process.env.NEXT_PUBLIC_DEBUG === 'true';

// Debug logger
const debug = {
  log: (...args: any[]) => DEBUG && console.log('[API Client]', ...args),
  error: (...args: any[]) => console.error('[API Client]', ...args),
  warn: (...args: any[]) => console.warn('[API Client]', ...args),
};

// Log configuration on load (always, for troubleshooting)
if (typeof window !== 'undefined') {
  console.log('🔧 Macrocomm API Client Configuration:');
  console.log('   API URL:', API_BASE_URL);
  console.log('   WebSocket URL:', WS_BASE_URL);
  console.log('   Debug Mode:', DEBUG ? 'ENABLED' : 'disabled');
}

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
  });
  
  return handleResponse<T>(response);
}

async function post<T>(endpoint: string, data?: any): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: defaultHeaders,
    body: data ? JSON.stringify(data) : undefined,
  });

  return handleResponse<T>(response);
}

async function del<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'DELETE',
    headers: defaultHeaders,
  });

  return handleResponse<T>(response);
}

async function uploadFile<T>(
  endpoint: string,
  file: File,
  additionalData?: Record<string, string>,
  onProgress?: (progress: number) => void
): Promise<T> {
  const uploadUrl = `${API_BASE_URL}${endpoint}`;
  debug.log(`📤 Uploading file: ${file.name} (${file.size} bytes) to ${uploadUrl}`);

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    // Add any additional form data
    if (additionalData) {
      Object.entries(additionalData).forEach(([key, value]) => {
        formData.append(key, value);
      });
    }

    xhr.upload.addEventListener('progress', (event) => {
      if (event.lengthComputable && onProgress) {
        const progress = Math.round((event.loaded / event.total) * 100);
        debug.log(`📤 Upload progress: ${progress}%`);
        onProgress(progress);
      }
    });

    xhr.addEventListener('load', () => {
      debug.log(`📤 Upload complete. Status: ${xhr.status}`);
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText));
        } catch {
          resolve(xhr.responseText as unknown as T);
        }
      } else {
        debug.error(`📤 Upload failed with status ${xhr.status}: ${xhr.statusText}`);
        reject(new ApiError(xhr.status, xhr.statusText));
      }
    });

    xhr.addEventListener('error', (event) => {
      debug.error(`📤 Upload network error. URL: ${uploadUrl}`, event);
      debug.error('💡 Check: 1) Backend running on port 8000? 2) CORS enabled? 3) Firewall?');
      reject(new ApiError(0, 'Network error'));
    });

    xhr.addEventListener('abort', () => {
      debug.warn('📤 Upload aborted');
      reject(new ApiError(0, 'Upload aborted'));
    });

    xhr.open('POST', uploadUrl);
    xhr.send(formData);
  });
}

// =============================================================================
// CHAT API - Connects to /api/chat and /ws/chat/stream
// =============================================================================

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  include_sources?: boolean;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sources?: Array<{
    document_name: string;
    chunk_text: string;
    similarity_score: number;
  }>;
  model: string;
  tokens_used?: number;
  response_time?: number;
  // Visualization fields from data analyst backend
  chart?: any; // Plotly chart data
  chart_title?: string;
  chart_description?: string;
  dashboard?: any; // Dashboard configuration with KPIs and charts
  table?: any; // Table data
  table_title?: string;
  kpi?: any; // KPI data
}

export const chatApi = {
  /**
   * Send a chat message via REST API
   * Endpoint: POST /api/chat
   */
  async send(message: string, conversationId?: string): Promise<ChatResponse> {
    return post<ChatResponse>('/api/chat', {
      message,
      conversation_id: conversationId,
      include_sources: true,
    });
  },

  /**
   * Get RAG system status
   * Endpoint: GET /api/rag/status
   */
  async getStatus(): Promise<any> {
    return get('/api/rag/status');
  },
};

// =============================================================================
// WEBSOCKET STREAMING CHAT
// =============================================================================

type StreamCallback = (chunk: string) => void;
type CompleteCallback = (response: ChatResponse) => void;
type ErrorCallback = (error: Error) => void;

export class ChatWebSocket {
  private ws: WebSocket | null = null;
  private onStream: StreamCallback;
  private onComplete: CompleteCallback;
  private onError: ErrorCallback;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 3;
  private conversationId?: string;
  
  constructor(
    onStream: StreamCallback,
    onComplete: CompleteCallback,
    onError: ErrorCallback,
    conversationId?: string
  ) {
    this.onStream = onStream;
    this.onComplete = onComplete;
    this.onError = onError;
    this.conversationId = conversationId;
  }
  
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        // Connect to the streaming WebSocket endpoint
        const wsUrl = `${WS_BASE_URL}/ws/chat/stream`;
        debug.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('✅ WebSocket connected to backend:', wsUrl);
          debug.log('🔌 WebSocket connection established successfully');
          this.reconnectAttempts = 0;
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Handle different message types from the backend
            // Backend sends: stream_token, stream_complete, thinking, system, error, response
            if (data.type === 'stream_token' || data.type === 'chunk' || data.type === 'stream') {
              // Streaming chunk - backend sends 'token' field
              this.onStream(data.token || data.content || data.chunk || '');
            } else if (data.type === 'stream_complete' || data.type === 'complete' || data.type === 'done') {
              // Streaming complete
              this.onComplete({
                response: data.response || data.full_response || '',
                conversation_id: data.conversation_id || this.conversationId || '',
                sources: data.sources,
                model: data.model || 'gpt-4o-mini',
                tokens_used: data.tokens_used,
                response_time: data.response_time,
                // Pass through visualization data
                chart: data.chart,
                chart_title: data.chart_title,
                chart_description: data.chart_description,
                dashboard: data.dashboard,
                table: data.table,
                table_title: data.table_title,
                kpi: data.kpi,
              });
            } else if (data.type === 'thinking') {
              // Backend is processing - ignore or show typing indicator
              console.log('Backend thinking...');
            } else if (data.type === 'system') {
              // System message (e.g., welcome message)
              console.log('System:', data.message);
            } else if (data.type === 'error') {
              this.onError(new Error(data.message || 'Unknown error'));
            } else if (data.type === 'response') {
              // Non-streaming response from /ws/chat endpoint
              this.onComplete({
                response: data.response || data.message || '',
                conversation_id: data.conversation_id || '',
                sources: data.sources,
                model: data.model || 'gpt-4o-mini',
                response_time: data.response_time,
              });
            } else if (data.response) {
              // Direct response (non-streaming fallback)
              this.onComplete({
                response: data.response,
                conversation_id: data.conversation_id || '',
                sources: data.sources,
                model: data.model || 'gpt-4o-mini',
              });
            } else if (typeof data === 'string') {
              // Plain text chunk
              this.onStream(data);
            }
          } catch (e) {
            // Raw text stream (not JSON)
            this.onStream(event.data);
          }
        };
        
        this.ws.onerror = (event) => {
          debug.error('❌ WebSocket error:', event);
          debug.error('💡 Check: 1) Backend running? 2) Port 8000 accessible? 3) Firewall?');
          debug.error(`   Attempted URL: ${WS_BASE_URL}/ws/chat/stream`);
          this.onError(new Error('WebSocket connection error'));
          reject(new Error('WebSocket connection error'));
        };

        this.ws.onclose = (event) => {
          debug.log(`🔌 WebSocket closed. Code: ${event.code}, Reason: ${event.reason || 'none'}, Clean: ${event.wasClean}`);
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            debug.log(`🔄 Reconnecting... attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
            setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
          }
        };
      } catch (e) {
        debug.error('❌ Failed to create WebSocket:', e);
        reject(e);
      }
    });
  }
  
  send(message: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      // IMPORTANT: Backend expects type: "chat" to process the message
      const payload = {
        type: "chat",
        message,
        conversation_id: this.conversationId,
        include_sources: true,
      };
      this.ws.send(JSON.stringify(payload));
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
// DOCUMENT API - Connects to /api/documents/*
// =============================================================================

export interface Document {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  upload_date: string;
  status: string;
  error_message?: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export const documentApi = {
  /**
   * List all documents
   * Endpoint: GET /api/documents/list
   */
  async list(): Promise<DocumentListResponse> {
    return get<DocumentListResponse>('/api/documents/list');
  },

  /**
   * Upload a document
   * Endpoint: POST /api/upload (backend uses /api/upload, not /api/documents/upload)
   */
  async upload(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<any> {
    return uploadFile('/api/upload', file, undefined, onProgress);
  },

  /**
   * Delete a document
   * Endpoint: DELETE /api/documents/{document_id}
   */
  async delete(documentId: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}`, {
      method: 'DELETE',
      headers: defaultHeaders,
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to delete document');
    }
  },
};

// =============================================================================
// ANALYTICS API - Connects to /api/analytics/*
// =============================================================================

export interface AnalyticsSummary {
  total_queries: number;
  total_documents: number;
  total_chunks: number;
  total_conversations: number;
  avg_response_time: number;
  total_tokens_used: number;
  total_cost: number;
  queries_today: number;
  queries_this_week: number;
  queries_this_month: number;
}

export interface BudgetAlert {
  status: string;
  daily_used: number;
  daily_budget: number;
  daily_percentage: number;
  monthly_used: number;
  monthly_budget: number;
  monthly_percentage: number;
  alerts: string[];
}

export const analyticsApi = {
  /**
   * Get analytics summary
   * Endpoint: GET /api/analytics/summary
   */
  async getSummary(): Promise<AnalyticsSummary> {
    return get<AnalyticsSummary>('/api/analytics/summary');
  },

  /**
   * Get budget alerts
   * Endpoint: GET /api/analytics/budget-alert
   */
  async getBudgetAlert(dailyBudget = 10, monthlyBudget = 300): Promise<BudgetAlert> {
    return get<BudgetAlert>('/api/analytics/budget-alert', {
      daily_budget: String(dailyBudget),
      monthly_budget: String(monthlyBudget),
    });
  },

  /**
   * Get query history
   * Endpoint: GET /api/analytics/queries
   */
  async getQueryHistory(limit = 50): Promise<any[]> {
    return get('/api/analytics/queries', { limit: String(limit) });
  },
};

// =============================================================================
// CONVERSATION API - Connects to /api/conversations
// =============================================================================

export interface Conversation {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export const conversationApi = {
  /**
   * List all conversations
   * Endpoint: GET /api/conversations
   */
  async list(): Promise<Conversation[]> {
    return get<Conversation[]>('/api/conversations');
  },

  /**
   * Get conversation by ID
   * Endpoint: GET /api/conversations/{id}
   */
  async get(conversationId: string): Promise<any> {
    return get(`/api/conversations/${conversationId}`);
  },

  /**
   * Get messages in a conversation
   * Endpoint: GET /api/conversations/{id}/messages
   */
  async getMessages(conversationId: string): Promise<any[]> {
    return get(`/api/conversations/${conversationId}/messages`);
  },
};

// =============================================================================
// SESSION API - For Data Analyst features
// =============================================================================

export interface DataProfile {
  columns: Array<{
    name: string;
    type: string;
    semantic_type: string;
    missing_count: number;
    missing_percentage: number;
    unique_count: number;
    sample_values: any[];
    statistics?: {
      min?: number;
      max?: number;
      mean?: number;
      median?: number;
      std?: number;
      q1?: number;
      q3?: number;
    };
  }>;
  row_count: number;
  column_count: number;
  quality_score: number;
  quality_level: string;
  summary: string;
}

export interface ForecastResult {
  method: string;
  forecast_values: number[];
  forecast_dates: string[];
  confidence_lower: number[];
  confidence_upper: number[];
  confidence_level: number;
  metrics: {
    mae: number;
    rmse: number;
    mape: number;
  };
  trend_direction: string;
  seasonality_detected: boolean;
}

export interface StatisticalResult {
  test_type: string;
  test_statistic: number;
  p_value: number;
  significant: boolean;
  interpretation: string;
  effect_size?: number;
  confidence_interval?: [number, number];
  additional_info?: Record<string, any>;
}

export interface InsightResult {
  type: string;
  priority: string;
  category: string;
  title: string;
  description: string;
  metric?: string;
  value?: number;
  change?: number;
  recommendation?: string;
}

export interface AnalysisSession {
  id: string;
  created_at: string;
  data_loaded: boolean;
  file_name?: string;
  row_count?: number;
  column_count?: number;
}

export const sessionApi = {
  /**
   * Create a new analysis session
   * Endpoint: POST /api/sessions
   */
  async create(userId?: string): Promise<AnalysisSession> {
    return post('/api/sessions', { user_id: userId });
  },

  /**
   * Get session info
   * Endpoint: GET /api/sessions/{id}
   */
  async get(sessionId: string): Promise<AnalysisSession> {
    return get(`/api/sessions/${sessionId}`);
  },

  /**
   * Upload file to session
   * Endpoint: POST /api/sessions/{id}/upload
   */
  async uploadFile(
    sessionId: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<{ success: boolean; file_name: string; rows: number; columns: number; dataset_id?: string }> {
    return uploadFile(`/api/sessions/${sessionId}/upload`, file, undefined, onProgress);
  },

  /**
   * Load active dataset from DatasetManager into session
   * Endpoint: POST /api/sessions/{id}/load-active-dataset
   */
  async loadActiveDataset(
    sessionId: string
  ): Promise<{ success: boolean; message: string; file_name: string; rows: number; columns: number; dataset_id: string }> {
    return post(`/api/sessions/${sessionId}/load-active-dataset`, {});
  },

  /**
   * Get data profile for session
   * Endpoint: GET /api/sessions/{id}/profile
   */
  async getProfile(sessionId: string): Promise<DataProfile> {
    return get(`/api/sessions/${sessionId}/profile`);
  },

  /**
   * Get data preview (first N rows)
   * Endpoint: GET /api/sessions/{id}/preview
   */
  async getPreview(sessionId: string, limit = 100): Promise<{ columns: string[]; data: any[][] }> {
    return get(`/api/sessions/${sessionId}/preview`, { limit: String(limit) });
  },

  /**
   * Run forecast on a column
   * Endpoint: POST /api/sessions/{id}/forecast
   */
  async forecast(
    sessionId: string,
    column: string,
    periods: number,
    method?: string
  ): Promise<ForecastResult> {
    return post(`/api/sessions/${sessionId}/forecast`, {
      column,
      periods,
      method: method || 'auto',
    });
  },

  /**
   * Run statistical analysis
   * Endpoint: POST /api/sessions/{id}/statistics
   */
  async runStatistics(
    sessionId: string,
    testType: string,
    columns: string[],
    options?: Record<string, any>
  ): Promise<StatisticalResult> {
    return post(`/api/sessions/${sessionId}/statistics`, {
      test_type: testType,
      columns,
      ...options,
    });
  },

  /**
   * Get AI-generated insights
   * Endpoint: GET /api/sessions/{id}/insights
   */
  async getInsights(sessionId: string): Promise<InsightResult[]> {
    return get(`/api/sessions/${sessionId}/insights`);
  },

  /**
   * Get chart recommendations
   * Endpoint: POST /api/sessions/{id}/recommend-charts
   */
  async recommendCharts(
    sessionId: string,
    columns?: string[]
  ): Promise<Array<{ chart_type: string; score: number; explanation: string }>> {
    return post(`/api/sessions/${sessionId}/recommend-charts`, { columns });
  },

  /**
   * Generate a chart
   * Endpoint: POST /api/sessions/{id}/chart
   */
  async generateChart(
    sessionId: string,
    chartType: string,
    columns: string[],
    options?: Record<string, any>
  ): Promise<{ chart_data: any; chart_config: any }> {
    return post(`/api/sessions/${sessionId}/chart`, {
      chart_type: chartType,
      columns,
      ...options,
    });
  },

  /**
   * Send query to session (natural language)
   * Endpoint: POST /api/sessions/{id}/query
   */
  async query(sessionId: string, query: string): Promise<any> {
    return post(`/api/sessions/${sessionId}/query`, { query });
  },

  /**
   * Export data/analysis results
   * Endpoint: POST /api/sessions/{id}/export
   */
  async export(
    sessionId: string,
    format: 'csv' | 'excel' | 'json' | 'pdf'
  ): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/sessions/${sessionId}/export`, {
      method: 'POST',
      headers: defaultHeaders,
      body: JSON.stringify({ format }),
    });
    if (!response.ok) {
      throw new ApiError(response.status, 'Export failed');
    }
    return response.blob();
  },
};

// Need to expose API_BASE_URL for the export function
const API_BASE_URL_EXPORT = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// =============================================================================
// REPORTS & ALERTS API - Tier 2 Feature
// =============================================================================

export interface ScheduledReport {
  id: string;
  name: string;
  description: string;
  frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly';
  next_run: string;
  last_run?: string;
  recipients: string[];
  metrics: string[];
  format: 'pdf' | 'excel' | 'html';
  is_active: boolean;
  created_at: string;
}

export interface Alert {
  id: string;
  name: string;
  metric: string;
  operator: 'greater_than' | 'less_than' | 'equals' | 'change_by' | 'change_by_percent';
  threshold: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  channels: ('email' | 'slack' | 'teams' | 'webhook')[];
  recipients: string[];
  is_active: boolean;
  last_triggered?: string;
  trigger_count: number;
  created_at: string;
}

export interface AlertHistory {
  id: string;
  alert_id: string;
  alert_name: string;
  triggered_at: string;
  value: number;
  threshold: number;
  status: 'triggered' | 'resolved' | 'acknowledged';
  message: string;
}

export const reportsApi = {
  /**
   * List all scheduled reports
   */
  async listReports(): Promise<ScheduledReport[]> {
    return get('/api/reports');
  },

  /**
   * Create a new scheduled report
   */
  async createReport(report: Partial<ScheduledReport>): Promise<ScheduledReport> {
    return post('/api/reports', report);
  },

  /**
   * Update a scheduled report
   */
  async updateReport(id: string, report: Partial<ScheduledReport>): Promise<ScheduledReport> {
    return post(`/api/reports/${id}`, report);
  },

  /**
   * Delete a scheduled report
   */
  async deleteReport(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/reports/${id}`, {
      method: 'DELETE',
      headers: defaultHeaders,
    });
    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to delete report');
    }
  },

  /**
   * Run a report immediately
   */
  async runReport(id: string): Promise<{ success: boolean; message: string }> {
    return post(`/api/reports/${id}/run`, {});
  },

  /**
   * List all alerts
   */
  async listAlerts(): Promise<Alert[]> {
    return get('/api/alerts');
  },

  /**
   * Create a new alert
   */
  async createAlert(alert: Partial<Alert>): Promise<Alert> {
    return post('/api/alerts', alert);
  },

  /**
   * Update an alert
   */
  async updateAlert(id: string, alert: Partial<Alert>): Promise<Alert> {
    return post(`/api/alerts/${id}`, alert);
  },

  /**
   * Delete an alert
   */
  async deleteAlert(id: string): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/alerts/${id}`, {
      method: 'DELETE',
      headers: defaultHeaders,
    });
    if (!response.ok) {
      throw new ApiError(response.status, 'Failed to delete alert');
    }
  },

  /**
   * Get alert history
   */
  async getAlertHistory(limit = 50): Promise<AlertHistory[]> {
    return get('/api/alerts/history', { limit: String(limit) });
  },

  /**
   * Acknowledge an alert
   */
  async acknowledgeAlert(historyId: string): Promise<AlertHistory> {
    return post(`/api/alerts/history/${historyId}/acknowledge`, {});
  },
};

// =============================================================================
// COLLABORATION API - Tier 2 Feature
// =============================================================================

export interface Workspace {
  id: string;
  name: string;
  description: string;
  icon: string;
  member_count: number;
  resource_count: number;
  created_at: string;
  is_default: boolean;
}

export interface WorkspaceMember {
  id: string;
  name: string;
  email: string;
  avatar?: string;
  role: 'owner' | 'admin' | 'editor' | 'viewer';
  is_online: boolean;
  last_active?: string;
}

export interface SharedResource {
  id: string;
  name: string;
  type: 'dashboard' | 'analysis' | 'report' | 'query';
  description: string;
  visibility: 'private' | 'team' | 'organization' | 'public';
  owner_id: string;
  workspace_id: string;
  created_at: string;
  updated_at: string;
  view_count: number;
  like_count: number;
  comment_count: number;
}

export interface Comment {
  id: string;
  resource_id: string;
  author_id: string;
  content: string;
  mentions: string[];
  created_at: string;
  reply_count: number;
  like_count: number;
}

export const collaborationApi = {
  /**
   * List all workspaces
   */
  async listWorkspaces(): Promise<Workspace[]> {
    return get('/api/workspaces');
  },

  /**
   * Create a new workspace
   */
  async createWorkspace(workspace: Partial<Workspace>): Promise<Workspace> {
    return post('/api/workspaces', workspace);
  },

  /**
   * Get workspace members
   */
  async getWorkspaceMembers(workspaceId: string): Promise<WorkspaceMember[]> {
    return get(`/api/workspaces/${workspaceId}/members`);
  },

  /**
   * Add member to workspace
   */
  async addWorkspaceMember(
    workspaceId: string,
    email: string,
    role: WorkspaceMember['role']
  ): Promise<WorkspaceMember> {
    return post(`/api/workspaces/${workspaceId}/members`, { email, role });
  },

  /**
   * List shared resources in a workspace
   */
  async listResources(workspaceId: string): Promise<SharedResource[]> {
    return get(`/api/workspaces/${workspaceId}/resources`);
  },

  /**
   * Share a resource
   */
  async shareResource(
    resourceId: string,
    visibility: SharedResource['visibility'],
    sharedWith?: string[]
  ): Promise<SharedResource> {
    return post(`/api/resources/${resourceId}/share`, { visibility, shared_with: sharedWith });
  },

  /**
   * Get resource comments
   */
  async getComments(resourceId: string): Promise<Comment[]> {
    return get(`/api/resources/${resourceId}/comments`);
  },

  /**
   * Add comment to resource
   */
  async addComment(resourceId: string, content: string, mentions?: string[]): Promise<Comment> {
    return post(`/api/resources/${resourceId}/comments`, { content, mentions });
  },

  /**
   * Get activity feed
   */
  async getActivityFeed(workspaceId?: string, limit = 50): Promise<any[]> {
    const params: Record<string, string> = { limit: String(limit) };
    if (workspaceId) params.workspace_id = workspaceId;
    return get('/api/activity', params);
  },
};

// =============================================================================
// DATA TRANSFORMATION API - Tier 2 Feature
// =============================================================================

export interface TransformationStep {
  id: string;
  type: string;
  column?: string;
  config: Record<string, any>;
  description: string;
  is_enabled: boolean;
}

export interface TransformationPipeline {
  id: string;
  name: string;
  session_id: string;
  steps: TransformationStep[];
  created_at: string;
  updated_at: string;
}

export interface DataQualityIssue {
  column: string;
  type: 'missing' | 'duplicate' | 'outlier' | 'invalid' | 'inconsistent';
  severity: 'low' | 'medium' | 'high';
  count: number;
  description: string;
  suggestion: string;
}

export const transformApi = {
  /**
   * Get data quality issues for a session
   */
  async getQualityIssues(sessionId: string): Promise<DataQualityIssue[]> {
    return get(`/api/sessions/${sessionId}/quality`);
  },

  /**
   * Apply transformation to session data
   */
  async applyTransformation(
    sessionId: string,
    step: Partial<TransformationStep>
  ): Promise<{ success: boolean; preview: any }> {
    return post(`/api/sessions/${sessionId}/transform`, step);
  },

  /**
   * Apply multiple transformations (pipeline)
   */
  async applyPipeline(
    sessionId: string,
    steps: Partial<TransformationStep>[]
  ): Promise<{ success: boolean; row_count: number; column_count: number }> {
    return post(`/api/sessions/${sessionId}/transform/pipeline`, { steps });
  },

  /**
   * Get transformation preview
   */
  async getPreview(
    sessionId: string,
    step: Partial<TransformationStep>
  ): Promise<{ before: any[]; after: any[] }> {
    return post(`/api/sessions/${sessionId}/transform/preview`, step);
  },

  /**
   * Save transformation pipeline
   */
  async savePipeline(
    sessionId: string,
    name: string,
    steps: Partial<TransformationStep>[]
  ): Promise<TransformationPipeline> {
    return post(`/api/sessions/${sessionId}/pipelines`, { name, steps });
  },

  /**
   * List saved pipelines
   */
  async listPipelines(sessionId: string): Promise<TransformationPipeline[]> {
    return get(`/api/sessions/${sessionId}/pipelines`);
  },

  /**
   * Auto-fix quality issues
   */
  async autoFix(
    sessionId: string,
    issues: DataQualityIssue[]
  ): Promise<{ success: boolean; fixed_count: number }> {
    return post(`/api/sessions/${sessionId}/quality/autofix`, { issues });
  },
};

// =============================================================================
// NATURAL LANGUAGE QUERY API - Tier 2 Feature
// =============================================================================

export interface NLQueryResult {
  natural_query: string;
  generated_sql: string;
  explanation: string;
  columns: string[];
  data: any[][];
  row_count: number;
  execution_time: number;
}

export const nlQueryApi = {
  /**
   * Convert natural language to SQL
   */
  async generateSql(
    sessionId: string,
    query: string
  ): Promise<{ sql: string; explanation: string }> {
    return post(`/api/sessions/${sessionId}/nl-to-sql`, { query });
  },

  /**
   * Execute generated SQL
   */
  async executeSql(
    sessionId: string,
    sql: string
  ): Promise<NLQueryResult> {
    return post(`/api/sessions/${sessionId}/execute-sql`, { sql });
  },

  /**
   * Get query suggestions based on data
   */
  async getSuggestions(sessionId: string): Promise<string[]> {
    return get(`/api/sessions/${sessionId}/query-suggestions`);
  },
};

// =============================================================================
// HEALTH CHECK
// =============================================================================

export interface HealthStatus {
  status: string;
  timestamp: number;
  service: string;
  version: string;
  components: {
    rag_system: { status: string; initialized: string };
    vector_store: { status: string };
    llm_service: { status: string; provider: string };
    websocket: { status: string; connections: string };
    conversations: { status: string; total: string };
    analytics: { status: string };
    citations: { status: string };
    multi_tenant: { status: string };
    document_scopes: { status: string };
  };
}

export async function checkHealth(): Promise<HealthStatus> {
  return get<HealthStatus>('/health');
}

export async function checkApiHealth(): Promise<boolean> {
  try {
    const health = await checkHealth();
    return health.status === 'healthy';
  } catch {
    return false;
  }
}

// =============================================================================
// 📊 UNIFIED DATASET API (Upload Once, Use Everywhere)
// =============================================================================

export interface DatasetMetadata {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  file_type: string;
  upload_time: string;
  status: 'pending' | 'processing' | 'ready' | 'error';
  row_count: number;
  column_count: number;
  columns: Array<{
    name: string;
    dtype: string;
    non_null_count: number;
    null_count: number;
    unique_count: number;
    sample_values: any[];
    min_value?: number;
    max_value?: number;
    mean_value?: number;
    top_values?: Array<[string, number]>;
  }>;
  sheets?: string[];
  vector_chunks: number;
  is_active?: boolean;
  error_message?: string;
}

export interface DatasetUploadResponse {
  success: boolean;
  dataset_id: string;
  filename: string;
  file_size: number;
  file_type: string;
  row_count: number;
  column_count: number;
  columns: any[];
  vector_chunks: number;
  is_active: boolean;
  message: string;
}

export interface DatasetListResponse {
  datasets: DatasetMetadata[];
  total: number;
  active_dataset_id: string | null;
}

export const datasetApi = {
  /**
   * Upload a dataset for use across all features
   * Endpoint: POST /api/datasets/upload
   */
  async upload(
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<DatasetUploadResponse> {
    debug.log(`📤 Uploading dataset: ${file.name}`);

    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append('file', file);

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          const progress = Math.round((e.loaded / e.total) * 100);
          onProgress(progress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const response = JSON.parse(xhr.responseText);
          debug.log('✅ Dataset upload successful:', response);
          resolve(response);
        } else {
          const error = JSON.parse(xhr.responseText);
          debug.error('❌ Dataset upload failed:', error);
          reject(new ApiError(xhr.status, error.detail || 'Upload failed', error));
        }
      });

      xhr.addEventListener('error', () => {
        debug.error('❌ Dataset upload network error');
        reject(new Error('Network error during upload'));
      });

      xhr.open('POST', `${API_BASE_URL}/api/datasets/upload`);
      xhr.send(formData);
    });
  },

  /**
   * List all uploaded datasets
   * Endpoint: GET /api/datasets
   */
  async list(): Promise<DatasetListResponse> {
    debug.log('📋 Fetching dataset list');
    return get<DatasetListResponse>('/api/datasets');
  },

  /**
   * Get the active dataset
   * Endpoint: GET /api/datasets/active
   */
  async getActive(): Promise<{ active: boolean; dataset?: DatasetMetadata; is_tabular?: boolean }> {
    debug.log('📌 Fetching active dataset');
    return get('/api/datasets/active');
  },

  /**
   * Set the active dataset
   * Endpoint: POST /api/datasets/active
   */
  async setActive(datasetId: string): Promise<{ success: boolean; active_dataset?: DatasetMetadata }> {
    debug.log(`📌 Setting active dataset: ${datasetId}`);
    return post('/api/datasets/active', { dataset_id: datasetId });
  },

  /**
   * Get details for a specific dataset
   * Endpoint: GET /api/datasets/{dataset_id}
   */
  async get(datasetId: string): Promise<DatasetMetadata> {
    debug.log(`📊 Fetching dataset: ${datasetId}`);
    return get(`/api/datasets/${datasetId}`);
  },

  /**
   * Delete a dataset
   * Endpoint: DELETE /api/datasets/{dataset_id}
   */
  async delete(datasetId: string): Promise<{ success: boolean; deleted: string }> {
    debug.log(`🗑️ Deleting dataset: ${datasetId}`);
    return del(`/api/datasets/${datasetId}`);
  },

  /**
   * Get dataset data (paginated)
   * Endpoint: GET /api/datasets/{dataset_id}/data
   */
  async getData(
    datasetId: string,
    offset: number = 0,
    limit: number = 100,
    columns?: string[]
  ): Promise<{
    data: any[];
    total_rows: number;
    offset: number;
    limit: number;
    columns: string[];
  }> {
    debug.log(`📊 Fetching data for dataset: ${datasetId}`);
    const params: Record<string, string> = {
      offset: offset.toString(),
      limit: limit.toString(),
    };
    if (columns && columns.length > 0) {
      params.columns = columns.join(',');
    }
    return get(`/api/datasets/${datasetId}/data`, params);
  },

  /**
   * Get dataset manager statistics
   * Endpoint: GET /api/datasets/stats
   */
  async getStats(): Promise<{
    total_datasets: number;
    active_dataset_id: string | null;
    active_dataset_name: string | null;
    total_rows: number;
    total_vector_chunks: number;
  }> {
    debug.log('📈 Fetching dataset stats');
    return get('/api/datasets/stats');
  },
};

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export const api = {
  chat: chatApi,
  document: documentApi,
  analytics: analyticsApi,
  conversation: conversationApi,
  session: sessionApi,
  reports: reportsApi,
  collaboration: collaborationApi,
  transform: transformApi,
  nlQuery: nlQueryApi,
  dataset: datasetApi,
  checkHealth,
  checkApiHealth,
  ChatWebSocket,
};

export default api;