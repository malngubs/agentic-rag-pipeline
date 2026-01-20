/**
 * ============================================================================
 * ⚙️ ADMIN PORTAL - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Converted from admin.html to React component.
 * Font: Inter, Segoe UI (matching globals.css)
 * Features: Document management, analytics, system health
 */

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  FileText,
  Upload,
  Trash2,
  BarChart3,
  Activity,
  Users,
  Database,
  Settings,
  Home,
  MessageSquare,
  LayoutDashboard,
  Sparkles,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import { api } from '@/lib/api/client';

// Types
interface Document {
  id: string;
  filename: string;
  size: number;
  uploaded_at: string;
  chunks: number;
}

interface Analytics {
  total_queries: number;
  total_documents: number;
  avg_response_time: number;
  total_cost: number;
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

export default function AdminPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch all data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    await Promise.all([fetchDocuments(), fetchAnalytics(), fetchHealth()]);
    setLoading(false);
  };

  const fetchDocuments = async () => {
    try {
      const data = await api.documents.list();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const data = await api.analytics.summary();
      setAnalytics(data);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
    }
  };

  const fetchHealth = async () => {
    try {
      const data = await api.health();
      setHealth(data);
    } catch (error) {
      console.error('Failed to fetch health:', error);
      setError('Unable to connect to backend API');
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await api.documents.upload(file);
      await Promise.all([fetchDocuments(), fetchAnalytics()]);
    } catch (error) {
      console.error('Upload failed:', error);
      setError('Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteDocument = async (docId: string) => {
    if (!confirm('Delete this document?')) return;

    try {
      await api.documents.delete(docId);
      await Promise.all([fetchDocuments(), fetchAnalytics()]);
    } catch (error) {
      console.error('Delete failed:', error);
      setError('Failed to delete document');
    }
  };

  const getHealthStatus = (component: HealthComponent | undefined) => {
    if (!component) return { icon: AlertCircle, color: 'text-foreground-muted', label: 'Unknown' };
    if (component.status === 'healthy') return { icon: CheckCircle2, color: 'text-success', label: 'Operational' };
    if (component.status === 'degraded') return { icon: AlertTriangle, color: 'text-warning', label: 'Degraded' };
    if (component.status === 'disabled') return { icon: AlertCircle, color: 'text-foreground-muted', label: 'Disabled' };
    return { icon: AlertCircle, color: 'text-error', label: 'Error' };
  };

  return (
    <div className="flex h-screen overflow-hidden">
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
            href="#"
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
              className="flex items-center gap-2 px-4 py-2 rounded-lg border border-border hover:bg-surface-hover transition-colors disabled:opacity-50"
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
          {analytics && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="glass border border-white/10 p-6 rounded-xl">
                <div className="flex items-center gap-3 mb-2">
                  <FileText className="w-5 h-5 text-brand-500" />
                  <p className="text-sm text-foreground-muted">Documents</p>
                </div>
                <p className="text-2xl font-bold text-foreground">{analytics.total_documents}</p>
              </div>

              <div className="glass border border-white/10 p-6 rounded-xl">
                <div className="flex items-center gap-3 mb-2">
                  <MessageSquare className="w-5 h-5 text-brand-500" />
                  <p className="text-sm text-foreground-muted">Total Queries</p>
                </div>
                <p className="text-2xl font-bold text-foreground">{analytics.total_queries}</p>
              </div>

              <div className="glass border border-white/10 p-6 rounded-xl">
                <div className="flex items-center gap-3 mb-2">
                  <Activity className="w-5 h-5 text-brand-500" />
                  <p className="text-sm text-foreground-muted">Avg Response</p>
                </div>
                <p className="text-2xl font-bold text-foreground">{analytics.avg_response_time.toFixed(2)}s</p>
              </div>

              <div className="glass border border-white/10 p-6 rounded-xl">
                <div className="flex items-center gap-3 mb-2">
                  <Database className="w-5 h-5 text-brand-500" />
                  <p className="text-sm text-foreground-muted">Total Cost</p>
                </div>
                <p className="text-2xl font-bold text-foreground">${analytics.total_cost.toFixed(4)}</p>
              </div>
            </div>
          )}

          {/* Documents Section */}
          <div className="glass border border-white/10 rounded-xl p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-foreground">Documents</h2>
              <label className="glossy-button px-4 py-2 rounded-lg text-white font-medium cursor-pointer">
                <Upload className="w-4 h-4 inline mr-2" />
                {uploading ? 'Uploading...' : 'Upload Document'}
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf,.txt,.docx,.csv,.xlsx"
                  onChange={handleFileUpload}
                  disabled={uploading}
                />
              </label>
            </div>

            {loading ? (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-brand-600"></div>
                <p className="mt-4 text-foreground-muted">Loading documents...</p>
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
                <p className="text-foreground-muted">No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-2">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="flex items-center gap-4 p-4 bg-surface rounded-lg border border-border hover:bg-surface-hover transition-colors"
                  >
                    <FileText className="w-5 h-5 text-brand-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">{doc.filename}</p>
                      <p className="text-sm text-foreground-muted">
                        {doc.chunks} chunks • {(doc.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="p-2 text-error hover:bg-error/10 rounded-lg transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Error Banner */}
          {error && (
            <div className="glass border border-error/30 bg-error/10 rounded-xl p-4 flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-error flex-shrink-0" />
              <p className="text-error">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-error hover:text-error/80"
              >
                ×
              </button>
            </div>
          )}

          {/* System Health */}
          <div className="glass border border-white/10 rounded-xl p-6">
            <h2 className="text-lg font-semibold text-foreground mb-6">System Health</h2>
            {!health ? (
              <div className="text-center py-8">
                {loading ? (
                  <>
                    <Loader2 className="w-8 h-8 animate-spin mx-auto text-brand-500" />
                    <p className="mt-4 text-foreground-muted">Checking system health...</p>
                  </>
                ) : (
                  <>
                    <AlertCircle className="w-8 h-8 mx-auto text-error" />
                    <p className="mt-4 text-error">Unable to connect to backend</p>
                  </>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {(() => {
                  const backendStatus = getHealthStatus({ status: health.status === 'healthy' ? 'healthy' : 'degraded' });
                  const BackendIcon = backendStatus.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <BackendIcon className={`w-5 h-5 ${backendStatus.color}`} />
                        <span className="text-foreground">Backend API</span>
                      </div>
                      <span className={`text-sm ${backendStatus.color}`}>{backendStatus.label}</span>
                    </div>
                  );
                })()}
                {(() => {
                  const vectorStatus = getHealthStatus(health.components?.vector_store);
                  const VectorIcon = vectorStatus.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <VectorIcon className={`w-5 h-5 ${vectorStatus.color}`} />
                        <span className="text-foreground">Vector Database (Qdrant)</span>
                      </div>
                      <span className={`text-sm ${vectorStatus.color}`}>{vectorStatus.label}</span>
                    </div>
                  );
                })()}
                {(() => {
                  const llmStatus = getHealthStatus(health.components?.llm_service);
                  const LlmIcon = llmStatus.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <LlmIcon className={`w-5 h-5 ${llmStatus.color}`} />
                        <span className="text-foreground">OpenAI API</span>
                        {health.components?.llm_service?.provider && (
                          <span className="text-xs text-foreground-muted">({health.components.llm_service.provider})</span>
                        )}
                      </div>
                      <span className={`text-sm ${llmStatus.color}`}>{llmStatus.label}</span>
                    </div>
                  );
                })()}
                {(() => {
                  const ragStatus = getHealthStatus(health.components?.rag_system);
                  const RagIcon = ragStatus.icon;
                  return (
                    <div className="flex items-center justify-between p-3 bg-surface rounded-lg border border-border">
                      <div className="flex items-center gap-3">
                        <RagIcon className={`w-5 h-5 ${ragStatus.color}`} />
                        <span className="text-foreground">RAG System</span>
                      </div>
                      <span className={`text-sm ${ragStatus.color}`}>{ragStatus.label}</span>
                    </div>
                  );
                })()}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
