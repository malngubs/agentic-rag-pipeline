/**
 * ============================================================================
 * 📋 TYPE DEFINITIONS - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Comprehensive TypeScript types for the frontend application.
 * These types mirror the backend API responses and internal state.
 */

// =============================================================================
// UTILITY TYPES
// =============================================================================

/** Generic API response wrapper */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

/** Pagination parameters */
export interface PaginationParams {
  page: number;
  limit: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/** Paginated response */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  hasMore: boolean;
}

// =============================================================================
// SESSION TYPES
// =============================================================================

/** Analysis session status */
export type SessionStatus = 'active' | 'idle' | 'processing' | 'error' | 'expired';

/** Analysis session */
export interface Session {
  id: string;
  createdAt: string;
  lastActive: string;
  status: SessionStatus;
  dataName?: string;
  rowCount?: number;
  columnCount?: number;
  columns?: string[];
}

/** Session creation response */
export interface CreateSessionResponse {
  sessionId: string;
  status: SessionStatus;
  createdAt: string;
}

// =============================================================================
// CHAT TYPES
// =============================================================================

/** Message role */
export type MessageRole = 'user' | 'assistant' | 'system';

/** Message status */
export type MessageStatus = 'sending' | 'sent' | 'streaming' | 'complete' | 'error';

/** Chat message */
export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: string;
  status: MessageStatus;
  
  // Optional metadata
  intent?: string;
  confidence?: number;
  executionTime?: number;
  
  // Artifacts attached to message
  charts?: ChartData[];
  dashboard?: DashboardData;
  insights?: string[];
  dataPreview?: DataPreview;
  
  // Error info
  error?: string;
}

/** Data preview */
export interface DataPreview {
  columns: string[];
  rows: Record<string, any>[];
  totalRows: number;
  displayedRows: number;
}

/** Query intent types */
export type QueryIntent =
  | 'load_data'
  | 'show_data'
  | 'filter_data'
  | 'sort_data'
  | 'aggregate_data'
  | 'profile_data'
  | 'statistics'
  | 'correlation'
  | 'trend_analysis'
  | 'anomaly_detection'
  | 'forecast'
  | 'create_chart'
  | 'recommend_chart'
  | 'create_dashboard'
  | 'export'
  | 'generate_insights'
  | 'explain'
  | 'summarize'
  | 'compare'
  | 'greeting'
  | 'help'
  | 'unknown';

/** Query result from backend */
export interface QueryResult {
  success: boolean;
  intent: QueryIntent;
  response: string;
  data?: any;
  charts?: ChartData[];
  dashboard?: DashboardData;
  insights?: string[];
  error?: string;
  executionTime: number;
}

// =============================================================================
// CHART TYPES
// =============================================================================

/** Chart type categories */
export type ChartCategory =
  | 'comparison'
  | 'correlation'
  | 'part_to_whole'
  | 'time_series'
  | 'distribution'
  | 'geospatial'
  | 'flow'
  | 'hierarchy'
  | 'specialized';

/** Chart types (subset of 84 available) */
export type ChartType =
  | 'bar_vertical'
  | 'bar_horizontal'
  | 'bar_grouped'
  | 'bar_stacked'
  | 'line'
  | 'line_multi'
  | 'area'
  | 'area_stacked'
  | 'pie'
  | 'donut'
  | 'scatter'
  | 'bubble'
  | 'heatmap'
  | 'treemap'
  | 'funnel'
  | 'waterfall'
  | 'radar'
  | 'histogram'
  | 'box'
  | 'violin'
  | 'kpi_card'
  | 'gauge'
  | 'table';

/** Chart data structure */
export interface ChartData {
  id: string;
  type: ChartType;
  title: string;
  description?: string;
  
  // Data configuration
  xColumn?: string;
  yColumn?: string;
  colorColumn?: string;
  sizeColumn?: string;
  
  // Data
  data?: any[];
  
  // Styling
  config?: ChartConfig;
  
  // HTML for rendering (from backend)
  html?: string;
  
  // AI-generated insights about this chart
  insights?: string[];
}

/** Chart configuration */
export interface ChartConfig {
  title?: string;
  subtitle?: string;
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  showDataLabels?: boolean;
  colorScheme?: string;
  theme?: 'light' | 'dark' | 'macrocomm';
  height?: number;
  width?: number;
}

/** Chart recommendation */
export interface ChartRecommendation {
  chartType: ChartType;
  category: ChartCategory;
  name: string;
  score: number;
  explanation: string;
  suggestedX?: string;
  suggestedY?: string;
}

// =============================================================================
// DASHBOARD TYPES
// =============================================================================

/** Dashboard widget */
export interface DashboardWidget {
  id: string;
  type: 'chart' | 'kpi' | 'text' | 'filter' | 'image';
  
  // Grid layout properties (for react-grid-layout)
  layout: {
    x: number;
    y: number;
    w: number;
    h: number;
    minW?: number;
    minH?: number;
    maxW?: number;
    maxH?: number;
    static?: boolean;
  };
  
  // Widget content
  content: ChartData | KPIData | TextData | FilterData;
}

/** KPI data */
export interface KPIData {
  id: string;
  title: string;
  value: number | string;
  format?: 'number' | 'currency' | 'percentage' | 'text';
  prefix?: string;
  suffix?: string;
  trend?: {
    direction: 'up' | 'down' | 'neutral';
    value: number;
    period: string;
  };
  icon?: string;
  color?: string;
}

/** Text widget data */
export interface TextData {
  id: string;
  content: string;
  format: 'plain' | 'markdown' | 'html';
}

/** Filter widget data */
export interface FilterData {
  id: string;
  column: string;
  type: 'select' | 'multiselect' | 'range' | 'date';
  values?: string[];
  selectedValues?: string[];
}

/** Dashboard data */
export interface DashboardData {
  id: string;
  title: string;
  description?: string;
  createdAt: string;
  updatedAt: string;
  
  // Widgets
  widgets: DashboardWidget[];
  
  // Settings
  settings?: {
    refreshInterval?: number;
    theme?: 'light' | 'dark' | 'macrocomm';
    gridCols?: number;
    rowHeight?: number;
  };
  
  // Export
  html?: string;
}

/** Dashboard template */
export interface DashboardTemplate {
  id: string;
  name: string;
  description: string;
  thumbnail?: string;
  category: string;
  widgets: Partial<DashboardWidget>[];
}

// =============================================================================
// FILE UPLOAD TYPES
// =============================================================================

/** Supported file types */
export type SupportedFileType =
  | 'csv'
  | 'xlsx'
  | 'xls'
  | 'json'
  | 'pdf'
  | 'txt'
  | 'docx'
  | 'pptx';

/** File upload status */
export type UploadStatus =
  | 'idle'
  | 'uploading'
  | 'processing'
  | 'complete'
  | 'error';

/** Uploaded file */
export interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: SupportedFileType;
  status: UploadStatus;
  progress: number;
  error?: string;
  
  // Post-processing info
  rowCount?: number;
  columnCount?: number;
  columns?: string[];
  previewData?: DataPreview;
}

// =============================================================================
// DATA PROFILE TYPES
// =============================================================================

/** Column profile */
export interface ColumnProfile {
  name: string;
  dtype: string;
  nonNullCount: number;
  nullCount: number;
  nullPercentage: number;
  uniqueCount: number;
  
  // Numeric stats
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  
  // Categorical stats
  topValues?: { value: string; count: number }[];
  
  // Quality flags
  issues?: string[];
}

/** Data profile */
export interface DataProfile {
  rowCount: number;
  columnCount: number;
  memoryUsage: string;
  qualityScore: number;
  columns: ColumnProfile[];
  correlations?: { col1: string; col2: string; value: number }[];
  insights?: string[];
}

// =============================================================================
// INSIGHT TYPES
// =============================================================================

/** Insight type */
export type InsightType =
  | 'trend'
  | 'anomaly'
  | 'correlation'
  | 'distribution'
  | 'comparison'
  | 'summary'
  | 'recommendation';

/** Insight */
export interface Insight {
  id: string;
  type: InsightType;
  title: string;
  description: string;
  importance: 'high' | 'medium' | 'low';
  confidence: number;
  relatedColumns?: string[];
  chart?: ChartData;
}

// =============================================================================
// UI STATE TYPES
// =============================================================================

/** Sidebar state */
export interface SidebarState {
  isOpen: boolean;
  isCollapsed: boolean;
  activeSection: 'chat' | 'dashboards' | 'documents' | 'settings';
}

/** Modal state */
export interface ModalState {
  isOpen: boolean;
  type: 'upload' | 'export' | 'settings' | 'confirm' | null;
  data?: any;
}

/** Toast notification */
export interface Toast {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

/** Theme */
export type Theme = 'light' | 'dark' | 'system';

// =============================================================================
// USER TYPES
// =============================================================================

/** User */
export interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user' | 'viewer';
  createdAt: string;
}

/** User preferences */
export interface UserPreferences {
  theme: Theme;
  language: string;
  dateFormat: string;
  numberFormat: string;
  defaultChartTheme: string;
}

// =============================================================================
// EXPORT TYPES
// =============================================================================

/** Export format */
export type ExportFormat = 'pdf' | 'png' | 'html' | 'xlsx' | 'csv' | 'json';

/** Export options */
export interface ExportOptions {
  format: ExportFormat;
  includeData?: boolean;
  includeCharts?: boolean;
  includeInsights?: boolean;
  paperSize?: 'A4' | 'Letter' | 'Tabloid';
  orientation?: 'portrait' | 'landscape';
}

/** Export result */
export interface ExportResult {
  success: boolean;
  format: ExportFormat;
  url?: string;
  filename?: string;
  error?: string;
}
