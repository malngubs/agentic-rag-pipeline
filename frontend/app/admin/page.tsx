/**
 * ============================================================================
 * ADMIN PORTAL - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * World-class admin interface with:
 * - Document management (upload, delete, list)
 * - Real-time analytics dashboard
 * - System health monitoring
 * - Robust error handling and notifications
 */

'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import Link from 'next/link';
import {
  FileText,
  Upload,
  Trash2,
  BarChart3,
  Activity,
  Users,
  Database,
  MessageSquare,
  LayoutDashboard,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  AlertTriangle,
  X,
  Check,
  FileUp,
} from 'lucide-react';
import { api } from '@/lib/api/client';

// =============================================================================
// TYPES - Matching backend DocumentResponse model
// =============================================================================

interface Document {
  doc_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_date: string;
  chunk_count: number;
  status: string;
  error_message?: string;
}

interface Analytics {
  total_queries: number;
  total_documents: number;
  avg_response_time: number;
  total_cost: number;
  total_chunks?: number;
  total_conversations?: number;
}

interface HealthComponent {
  status: string;
  initialized?: string;
  provider?: string;
  connections?: string;
  total?: string;
}

interface HealthResponse {
  status: string;
  timestamp?: number;
  service?: string;
  version?: string;
  components: {
    rag_system: HealthComponent;
    vector_store: HealthComponent;
    llm_service: HealthComponent;
    websocket: HealthComponent;
    conversations: HealthComponent;
    analytics: HealthComponent;
    citations: HealthComponent;
  };
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
  timestamp: number;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const SUPPORTED_FILE_TYPES = ['.pdf', '.txt', '.docx', '.csv', '.xlsx', '.xls'];
const MAX_FILE_SIZE_MB = 100;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;
const NOTIFICATION_DURATION_MS = 5000;

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

const formatDate = (dateString: string): string => {
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dateString;
  }
};

const generateId = (): string => Math.random().toString(36).substring(2, 9);

// =============================================================================
// MAIN COMPONENT
// =============================================================================

export default function AdminPage() {
  // State
  const [documents, setDocuments] = useState<Document[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [deletingIds, setDeletingIds] = useState<Set<string>>(new Set());
  const [notifications, setNotifications] = useState<Notification[]>([]);

  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);

  // =============================================================================
  // NOTIFICATION SYSTEM
  // =============================================================================

  const addNotification = useCallback((type: Notification['type'], message: string) => {
    const notification: Notification = {
      id: generateId(),
      type,
      message,
      timestamp: Date.now(),
    };
    setNotifications(prev => [...prev, notification]);

    // Auto-dismiss after duration
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== notification.id));
    }, NOTIFICATION_DURATION_MS);
  }, []);

  const dismissNotification = useCallback((id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  }, []);

  // =============================================================================
  // DATA FETCHING
  // =============================================================================

  const fetchDocuments = useCallback(async () => {
    try {
      const data = await api.documents.list();
      // Map backend response to our Document interface
      const docs: Document[] = (data.documents || []).map((doc: any) => ({
        doc_id: doc.doc_id || doc.id,
        filename: doc.filename || doc.name,
        file_type: doc.file_type || '',
        file_size: doc.file_size || doc.size || 0,
        upload_date: doc.upload_date || doc.uploaded_at || '',
        chunk_count: doc.chunk_count || doc.chunks || 0,
        status: doc.status || 'ready',
        error_message: doc.error_message,
      }));
      setDocuments(docs);
    } catch (error: any) {
      console.error('Failed to fetch documents:', error);
      // Don't show notification for initial load failure - health check will indicate issue
    }
  }, []);

  const fetchAnalytics = useCallback(async () => {
    try {
      const data = await api.analytics.summary();
      setAnalytics(data);
    } catch (error: any) {
      console.error('Failed to fetch analytics:', error);
    }
  }, []);

  const fetchHealth = useCallback(async () => {
    try {
      const data = await api.health();
      setHealth(data);
      return true;
    } catch (error: any) {
      console.error('Failed to fetch health:', error);
      setHealth(null);
      return false;
    }
  }, []);

  const loadData = useCallback(async () => {
    setLoading(true);
    const healthOk = await fetchHealth();
    if (healthOk) {
      await Promise.all([fetchDocuments(), fetchAnalytics()]);
    }
    setLoading(false);
  }, [fetchHealth, fetchDocuments, fetchAnalytics]);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // =============================================================================
  // FILE UPLOAD HANDLER
  // =============================================================================

  const validateFile = (file: File): { valid: boolean; error?: string } => {
    // Check file extension
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_FILE_TYPES.includes(extension)) {
      return {
        valid: false,
        error: `Unsupported file type "${extension}". Supported: ${SUPPORTED_FILE_TYPES.join(', ')}`,
      };
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return {
        valid: false,
        error: `File size (${formatFileSize(file.size)}) exceeds ${MAX_FILE_SIZE_MB}MB limit`,
      };
    }

    // Check for empty file
    if (file.size === 0) {
      return { valid: false, error: 'File is empty' };
    }

    return { valid: true };
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Reset input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }

    // Validate file
    const validation = validateFile(file);
    if (!validation.valid) {
      addNotification('error', validation.error!);
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      // Upload with progress tracking
      await api.documents.upload(file, (progress: number) => {
        setUploadProgress(progress);
      });

      addNotification('success', `Successfully uploaded "${file.name}"`);

      // Refresh data
      await Promise.all([fetchDocuments(), fetchAnalytics()]);
    } catch (error: any) {
      const errorMessage = error?.message || error?.data?.detail || 'Upload failed';
      addNotification('error', `Failed to upload "${file.name}": ${errorMessage}`);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  // =============================================================================
  // DELETE HANDLER
  // =============================================================================

  const handleDeleteDocument = async (doc: Document) => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${doc.filename}"?\n\nThis will remove the document and all ${doc.chunk_count} chunks from the system.`
    );

    if (!confirmed) return;

    // Add to deleting set for loading state
    setDeletingIds(prev => new Set(prev).add(doc.doc_id));

    try {
      await api.documents.delete(doc.doc_id);
      addNotification('success', `Successfully deleted "${doc.filename}"`);

      // Refresh data
      await Promise.all([fetchDocuments(), fetchAnalytics()]);
    } catch (error: any) {
      const errorMessage = error?.message || error?.data?.detail || 'Delete failed';
      addNotification('error', `Failed to delete "${doc.filename}": ${errorMessage}`);
    } finally {
      setDeletingIds(prev => {
        const next = new Set(prev);
        next.delete(doc.doc_id);
        return next;
      });
    }
  };

  // =============================================================================
  // HEALTH STATUS HELPER
  // =============================================================================

  const getHealthStatus = (component: HealthComponent | undefined) => {
    if (!component) {
      return { icon: AlertCircle, color: 'text-foreground-muted', label: 'Unknown' };
    }

    switch (component.status) {
      case 'healthy':
        return { icon: CheckCircle2, color: 'text-success', label: 'Operational' };
      case 'degraded':
        return { icon: AlertTriangle, color: 'text-warning', label: 'Degraded' };
      case 'disabled':
        return { icon: AlertCircle, color: 'text-foreground-muted', label: 'Disabled' };
      default:
        return { icon: AlertCircle, color: 'text-error', label: 'Error' };
    }
  };

  // =============================================================================
  // RENDER
  // =============================================================================

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2 max-w-md">
        {notifications.map(notification => (
          <div
            key={notification.id}
            className={`flex items-center gap-3 p-4 rounded-lg shadow-lg border backdrop-blur-sm animate-in slide-in-from-right ${
              notification.type === 'success'
                ? 'bg-success/10 border-success/30 text-success'
                : notification.type === 'error'
                ? 'bg-error/10 border-error/30 text-error'
                : 'bg-brand-500/10 border-brand-500/30 text-brand-500'
            }`}
          >
            {notification.type === 'success' ? (
              <Check className="w-5 h-5 flex-shrink-0" />
            ) : notification.type === 'error' ? (
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 flex-shrink-0" />
            )}
            <p className="flex-1 text-sm">{notification.message}</p>
            <button
              onClick={() => dismissNotification(notification.id)}
              className="flex-shrink-0 hover:opacity-70"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>

      {/* Sidebar */}
      <aside className="w-64 bg-surface border-r border-border flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl glossy-button flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-display font-bold text-foreground">Macrocomm</h1>
              <p className="text-xs text-foreground-muted">Admin Portal</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          <div className="text-xs font-semibold text-foreground-muted uppercase tracking-wider px-3 py-2">
            Main
          </div>
          <Link
            href="/"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-foreground-muted hover:bg-surface-hover hover:text-foreground transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            <span>BI Platform</span>
          </Link>
          <Link
            href="/dashboards"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-foreground-muted hover:bg-surface-hover hover:text-foreground transition-colors"
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Dashboards</span>
          </Link>

          <div className="text-xs font-semibold text-foreground-muted uppercase tracking-wider px-3 py-2 mt-6">
            Admin
          </div>
          <a
            href="#documents"
            className="flex items-center gap-3 px-3 py-2 rounded-lg bg-surface-hover text-foreground border-l-2 border-brand-600"
          >
            <FileText className="w-4 h-4" />
            <span>Documents</span>
          </a>
          <a
            href="#analytics"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-foreground-muted hover:bg-surface-hover hover:text-foreground transition-colors"
          >
            <BarChart3 className="w-4 h-4" />
            <span>Analytics</span>
          </a>
          <a
            href="#health"
            className="flex items-center gap-3 px-3 py-2 rounded-lg text-foreground-muted hover:bg-surface-hover hover:text-foreground transition-colors"
          >
            <Activity className="w-4 h-4" />
            <span>System Health</span>
          </a>
        </nav>

        {/* User */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full glossy-button flex items-center justify-center">
              <span className="text-sm font-semibold text-white">A</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">Admin</p>
              <p className="text-xs text-foreground-muted truncate">admin@macrocomm.ai</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="border-b border-border bg-background/80 backdrop-blur-sm px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-display font-semibold text-foreground">Admin Portal</h1>
              <p className="text-sm text-foreground-muted">Manage documents and monitor system</p>
            </div>
            <button
              onClick={loadData}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-surface-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              Refresh
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Stats Cards */}
          <div id="analytics" className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <FileText className="w-5 h-5 text-brand-500" />
                <p className="text-sm text-foreground-muted">Documents</p>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {loading ? '-' : analytics?.total_documents ?? documents.length}
              </p>
            </div>

            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <MessageSquare className="w-5 h-5 text-brand-500" />
                <p className="text-sm text-foreground-muted">Total Queries</p>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {loading ? '-' : analytics?.total_queries ?? 0}
              </p>
            </div>

            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <Activity className="w-5 h-5 text-brand-500" />
                <p className="text-sm text-foreground-muted">Avg Response</p>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {loading ? '-' : `${(analytics?.avg_response_time ?? 0).toFixed(2)}s`}
              </p>
            </div>

            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="flex items-center gap-3 mb-2">
                <Database className="w-5 h-5 text-brand-500" />
                <p className="text-sm text-foreground-muted">Total Cost</p>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {loading ? '-' : `$${(analytics?.total_cost ?? 0).toFixed(4)}`}
              </p>
            </div>
          </div>

          {/* Documents Section */}
          <div id="documents" className="glass border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-foreground">Documents</h2>
                <p className="text-sm text-foreground-muted">
                  Manage your uploaded documents ({documents.length} total)
                </p>
              </div>
              <label className={`glossy-button px-4 py-2 rounded-lg text-white font-medium cursor-pointer transition-all ${
                uploading ? 'opacity-50 cursor-not-allowed' : 'hover:scale-105'
              }`}>
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                    Uploading {uploadProgress}%
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 inline mr-2" />
                    Upload Document
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept={SUPPORTED_FILE_TYPES.join(',')}
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
              </label>
            </div>

            {/* Upload Progress Bar */}
            {uploading && (
              <div className="mb-6">
                <div className="h-2 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-600 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-foreground-muted mt-2">
                  Uploading... {uploadProgress}% complete
                </p>
              </div>
            )}

            {/* Documents List */}
            {loading ? (
              <div className="text-center py-12">
                <Loader2 className="w-8 h-8 animate-spin mx-auto text-brand-500" />
                <p className="mt-4 text-foreground-muted">Loading documents...</p>
              </div>
            ) : !health ? (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-error mx-auto mb-4" />
                <p className="text-error font-medium">Cannot connect to backend</p>
                <p className="text-sm text-foreground-muted mt-2">
                  Please ensure the backend server is running on port 8001
                </p>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12">
                <FileUp className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                <p className="text-foreground-muted font-medium">No documents uploaded yet</p>
                <p className="text-sm text-foreground-muted mt-2">
                  Upload a PDF, TXT, DOCX, CSV, or Excel file to get started
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => {
                  const isDeleting = deletingIds.has(doc.doc_id);
                  return (
                    <div
                      key={doc.doc_id}
                      className={`flex items-center gap-4 p-4 bg-surface rounded-lg border border-border transition-all ${
                        isDeleting ? 'opacity-50' : 'hover:bg-surface-hover'
                      }`}
                    >
                      <FileText className="w-5 h-5 text-brand-500 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-foreground truncate">{doc.filename}</p>
                        <p className="text-sm text-foreground-muted">
                          {doc.chunk_count} chunks &bull; {formatFileSize(doc.file_size)} &bull; {doc.file_type.toUpperCase()}
                        </p>
                        <p className="text-xs text-foreground-muted">
                          Uploaded {formatDate(doc.upload_date)}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {doc.status === 'ready' ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-success/10 text-success">
                            Ready
                          </span>
                        ) : doc.status === 'processing' ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-warning/10 text-warning flex items-center gap-1">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            Processing
                          </span>
                        ) : doc.status === 'error' ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-error/10 text-error" title={doc.error_message}>
                            Error
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-foreground-muted/10 text-foreground-muted">
                            {doc.status}
                          </span>
                        )}
                        <button
                          onClick={() => handleDeleteDocument(doc)}
                          disabled={isDeleting}
                          className="p-2 text-error hover:bg-error/10 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Delete document"
                        >
                          {isDeleting ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* System Health */}
          <div id="health" className="glass border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-semibold text-foreground">System Health</h2>
                <p className="text-sm text-foreground-muted">
                  Real-time status of backend services
                </p>
              </div>
              {health && (
                <span className={`px-3 py-1 text-sm rounded-full ${
                  health.status === 'healthy'
                    ? 'bg-success/10 text-success'
                    : 'bg-warning/10 text-warning'
                }`}>
                  {health.status === 'healthy' ? 'All Systems Operational' : 'Degraded Performance'}
                </span>
              )}
            </div>

            {!health && !loading ? (
              <div className="text-center py-8">
                <AlertCircle className="w-8 h-8 mx-auto text-error" />
                <p className="mt-4 text-error font-medium">Unable to connect to backend</p>
                <p className="text-sm text-foreground-muted mt-2">
                  Check if the backend is running at http://localhost:8001
                </p>
              </div>
            ) : !health && loading ? (
              <div className="text-center py-8">
                <Loader2 className="w-8 h-8 animate-spin mx-auto text-brand-500" />
                <p className="mt-4 text-foreground-muted">Checking system health...</p>
              </div>
            ) : health ? (
              <div className="space-y-3">
                {/* Backend API */}
                {(() => {
                  const status = getHealthStatus({ status: health.status });
                  const Icon = status.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <Icon className={`w-5 h-5 ${status.color}`} />
                        <span className="text-foreground">Backend API</span>
                        {health.version && (
                          <span className="text-xs text-foreground-muted">v{health.version}</span>
                        )}
                      </div>
                      <span className={`text-sm ${status.color}`}>{status.label}</span>
                    </div>
                  );
                })()}

                {/* Vector Store */}
                {(() => {
                  const status = getHealthStatus(health.components?.vector_store);
                  const Icon = status.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <Icon className={`w-5 h-5 ${status.color}`} />
                        <span className="text-foreground">Vector Database (Qdrant)</span>
                      </div>
                      <span className={`text-sm ${status.color}`}>{status.label}</span>
                    </div>
                  );
                })()}

                {/* LLM Service */}
                {(() => {
                  const status = getHealthStatus(health.components?.llm_service);
                  const Icon = status.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <Icon className={`w-5 h-5 ${status.color}`} />
                        <span className="text-foreground">OpenAI API</span>
                        {health.components?.llm_service?.provider && (
                          <span className="text-xs text-foreground-muted">
                            ({health.components.llm_service.provider})
                          </span>
                        )}
                      </div>
                      <span className={`text-sm ${status.color}`}>{status.label}</span>
                    </div>
                  );
                })()}

                {/* RAG System */}
                {(() => {
                  const status = getHealthStatus(health.components?.rag_system);
                  const Icon = status.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <Icon className={`w-5 h-5 ${status.color}`} />
                        <span className="text-foreground">RAG System</span>
                      </div>
                      <span className={`text-sm ${status.color}`}>{status.label}</span>
                    </div>
                  );
                })()}

                {/* WebSocket */}
                {(() => {
                  const status = getHealthStatus(health.components?.websocket);
                  const Icon = status.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <Icon className={`w-5 h-5 ${status.color}`} />
                        <span className="text-foreground">WebSocket</span>
                        {health.components?.websocket?.connections && (
                          <span className="text-xs text-foreground-muted">
                            ({health.components.websocket.connections} connections)
                          </span>
                        )}
                      </div>
                      <span className={`text-sm ${status.color}`}>{status.label}</span>
                    </div>
                  );
                })()}
              </div>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
