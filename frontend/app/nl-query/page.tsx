/**
 * ============================================================================
 * NATURAL LANGUAGE TO SQL - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Convert plain English questions into SQL queries:
 * - Natural language query input
 * - AI-powered SQL generation
 * - Query preview and editing
 * - Real-time results
 * - Query history and suggestions
 */

'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { api, AnalysisSession, DataProfile } from '@/lib/api/client';
import {
  MessageSquare,
  Database,
  Code,
  Play,
  Loader2,
  AlertCircle,
  X,
  Copy,
  Check,
  History,
  Sparkles,
  Upload,
  FileSpreadsheet,
  Table,
  ChevronRight,
  Edit3,
  Save,
  RotateCcw,
  Lightbulb,
  Search,
  ArrowRight,
  Wand2,
  Zap,
  BookOpen,
  Send,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

interface QueryHistoryItem {
  id: string;
  naturalLanguage: string;
  generatedSql: string;
  timestamp: Date;
  rowCount: number;
  executionTime: number;
}

interface QuerySuggestion {
  text: string;
  category: string;
}

interface QueryResult {
  columns: string[];
  data: any[][];
  rowCount: number;
  executionTime: number;
  generatedSql: string;
  explanation: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const QUERY_SUGGESTIONS: QuerySuggestion[] = [
  { text: 'Show me the top 10 customers by revenue', category: 'Ranking' },
  { text: 'What is the total sales by region?', category: 'Aggregation' },
  { text: 'Find all transactions over $10,000', category: 'Filtering' },
  { text: 'Calculate the average order value per month', category: 'Time Series' },
  { text: 'Compare this year vs last year sales', category: 'Comparison' },
  { text: 'Which products have the highest profit margin?', category: 'Analysis' },
  { text: 'Show revenue trend over the last 12 months', category: 'Trends' },
  { text: 'Find customers who havent ordered in 90 days', category: 'Segmentation' },
];

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const SuggestionChip: React.FC<{
  suggestion: QuerySuggestion;
  onClick: () => void;
}> = ({ suggestion, onClick }) => (
  <button
    onClick={onClick}
    className="group flex items-center gap-2 px-3 py-2 bg-surface border border-border rounded-lg hover:border-brand-500/50 hover:bg-brand-600/5 transition-all text-left"
  >
    <Lightbulb className="w-4 h-4 text-amber-500 group-hover:text-brand-500 transition-colors" />
    <span className="text-sm text-foreground">{suggestion.text}</span>
    <span className="ml-auto px-2 py-0.5 text-xs bg-surface-muted text-foreground-muted rounded">
      {suggestion.category}
    </span>
  </button>
);

const HistoryItem: React.FC<{
  item: QueryHistoryItem;
  onClick: () => void;
}> = ({ item, onClick }) => (
  <button
    onClick={onClick}
    className="w-full p-3 bg-surface border border-border rounded-lg hover:border-brand-500/50 transition-colors text-left"
  >
    <p className="text-sm text-foreground truncate mb-1">{item.naturalLanguage}</p>
    <div className="flex items-center gap-3 text-xs text-foreground-muted">
      <span>{item.rowCount} rows</span>
      <span className="w-1 h-1 rounded-full bg-foreground-muted" />
      <span>{item.executionTime}ms</span>
      <span className="w-1 h-1 rounded-full bg-foreground-muted" />
      <span>{new Date(item.timestamp).toLocaleTimeString()}</span>
    </div>
  </button>
);

const SqlEditor: React.FC<{
  sql: string;
  onChange: (sql: string) => void;
  onRun: () => void;
  isRunning: boolean;
  isEditing: boolean;
  onEditToggle: () => void;
  tableName?: string;
  explanation?: string;
}> = ({ sql, onChange, onRun, isRunning, isEditing, onEditToggle, tableName, explanation }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-surface border border-border rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-surface-muted border-b border-border">
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 text-brand-500" />
          <span className="text-sm font-medium text-foreground">Generated SQL</span>
          {tableName && (
            <span className="px-2 py-0.5 text-xs bg-emerald-500/10 text-emerald-600 rounded-full">
              Table: {tableName}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="flex items-center gap-1 px-2 py-1 text-xs text-foreground-muted hover:text-foreground transition-colors"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            onClick={onEditToggle}
            className={`flex items-center gap-1 px-2 py-1 text-xs transition-colors ${
              isEditing ? 'text-brand-500' : 'text-foreground-muted hover:text-foreground'
            }`}
          >
            <Edit3 className="w-3 h-3" />
            {isEditing ? 'Editing' : 'Edit'}
          </button>
        </div>
      </div>

      {/* AI Explanation for generated SQL */}
      {explanation && !isEditing && (
        <div className="px-4 py-3 bg-brand-600/5 border-b border-brand-500/10">
          <div className="flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-brand-500 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-foreground-secondary">{explanation}</p>
          </div>
        </div>
      )}

      <div className="p-4">
        {isEditing ? (
          <textarea
            value={sql}
            onChange={(e) => onChange(e.target.value)}
            className="w-full h-40 p-3 bg-background border border-border rounded-lg font-mono text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50 resize-none"
            spellCheck={false}
          />
        ) : (
          <pre className="font-mono text-sm text-foreground whitespace-pre-wrap overflow-x-auto">
            {sql || 'No SQL generated yet'}
          </pre>
        )}
      </div>
      <div className="flex items-center justify-between px-4 py-3 bg-surface-muted border-t border-border">
        {isEditing && (
          <p className="text-xs text-foreground-muted">
            You can modify the SQL query before running it
          </p>
        )}
        <div className={`flex items-center gap-2 ${!isEditing ? 'ml-auto' : ''}`}>
          <button
            onClick={onRun}
            disabled={isRunning || !sql}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isRunning ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Query
          </button>
        </div>
      </div>
    </div>
  );
};

const ResultsTable: React.FC<{
  result: QueryResult | null;
  isLoading: boolean;
}> = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="text-center">
          <Loader2 className="w-8 h-8 text-brand-500 animate-spin mx-auto mb-4" />
          <p className="text-foreground-muted">Executing query...</p>
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-16">
        <Table className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
        <p className="text-foreground-muted">Ask a question to see results</p>
      </div>
    );
  }

  return (
    <div>
      {/* Explanation */}
      {result.explanation && (
        <div className="mb-4 p-4 bg-brand-600/5 border border-brand-500/20 rounded-lg">
          <div className="flex items-start gap-3">
            <Sparkles className="w-5 h-5 text-brand-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-foreground mb-1">AI Explanation</p>
              <p className="text-sm text-foreground-secondary">{result.explanation}</p>
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 mb-4 text-sm text-foreground-muted">
        <span>{result.rowCount.toLocaleString()} rows</span>
        <span className="w-1 h-1 rounded-full bg-foreground-muted" />
        <span>{result.columns.length} columns</span>
        <span className="w-1 h-1 rounded-full bg-foreground-muted" />
        <span>{result.executionTime.toFixed(2)}ms</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-border rounded-lg">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-surface-muted border-b border-border">
              {result.columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-4 py-3 text-left font-semibold text-foreground whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {result.data.slice(0, 100).map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="border-b border-border/50 hover:bg-surface-hover transition-colors"
              >
                {row.map((cell, cellIdx) => (
                  <td key={cellIdx} className="px-4 py-3 text-foreground whitespace-nowrap">
                    {cell === null ? (
                      <span className="text-foreground-muted italic">null</span>
                    ) : typeof cell === 'number' ? (
                      cell.toLocaleString()
                    ) : (
                      String(cell)
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {result.rowCount > 100 && (
        <p className="text-xs text-foreground-muted mt-2 text-center">
          Showing first 100 of {result.rowCount.toLocaleString()} rows
        </p>
      )}
    </div>
  );
};

// =============================================================================
// MAIN NL QUERY PAGE
// =============================================================================

export default function NLQueryPage() {
  // Session state
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [profile, setProfile] = useState<DataProfile | null>(null);

  // Query state
  const [naturalQuery, setNaturalQuery] = useState('');
  const [generatedSql, setGeneratedSql] = useState('');
  const [result, setResult] = useState<QueryResult | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // History state
  const [queryHistory, setQueryHistory] = useState<QueryHistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);

  // UI state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isGenerating, setIsGenerating] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize session
  useEffect(() => {
    const initSession = async () => {
      try {
        const newSession = await api.session.create();
        setSession(newSession);
      } catch (err) {
        console.error('Failed to create session:', err);
      }
    };
    initSession();
  }, []);

  // Handle file upload
  const handleFileUpload = useCallback(async (file: File) => {
    if (!session?.id) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const uploadResult = await api.session.uploadFile(session.id, file, (progress) => {
        setUploadProgress(progress);
      });

      setSession({
        ...session,
        data_loaded: true,
        file_name: uploadResult.file_name,
        row_count: uploadResult.rows,
        column_count: uploadResult.columns,
      });

      // Load profile
      const profileData = await api.session.getProfile(session.id);
      setProfile(profileData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [session]);

  // Store the table name from SQL generation for reference
  const [tableName, setTableName] = useState<string>('');
  const [sqlExplanation, setSqlExplanation] = useState<string>('');

  // Generate SQL from natural language using the backend API
  const handleGenerateSql = useCallback(async () => {
    if (!session?.id || !naturalQuery.trim()) return;

    setIsGenerating(true);
    setError(null);
    setResult(null); // Clear previous results

    try {
      // Use the dedicated NL-to-SQL endpoint
      const response = await api.nlQuery.generateSql(session.id, naturalQuery);

      // Set the generated SQL and metadata
      setGeneratedSql(response.generated_sql);
      setTableName(response.table_name);
      setSqlExplanation(response.explanation);

    } catch (err: any) {
      const errorMessage = err?.message || err?.data?.detail || 'Failed to generate SQL';
      setError(errorMessage);
    } finally {
      setIsGenerating(false);
    }
  }, [session?.id, naturalQuery]);

  // Run the generated SQL using the backend execute-sql endpoint
  const handleRunSql = useCallback(async () => {
    if (!session?.id || !generatedSql) return;

    setIsRunning(true);
    setError(null);

    try {
      // Use the dedicated execute-sql endpoint
      const response = await api.nlQuery.executeSql(session.id, generatedSql);

      const queryResult: QueryResult = {
        columns: response.columns,
        data: response.data,
        rowCount: response.row_count,
        executionTime: response.execution_time,
        generatedSql,
        explanation: response.explanation,
      };

      setResult(queryResult);

      // Add to history
      const historyItem: QueryHistoryItem = {
        id: `query-${Date.now()}`,
        naturalLanguage: naturalQuery,
        generatedSql,
        timestamp: new Date(),
        rowCount: queryResult.rowCount,
        executionTime: queryResult.executionTime,
      };
      setQueryHistory(prev => [historyItem, ...prev.slice(0, 19)]);
    } catch (err: any) {
      const errorMessage = err?.message || err?.data?.detail || 'Query execution failed';
      setError(errorMessage);
    } finally {
      setIsRunning(false);
    }
  }, [session?.id, generatedSql, naturalQuery]);

  // Handle suggestion click
  const handleSuggestionClick = useCallback((suggestion: QuerySuggestion) => {
    setNaturalQuery(suggestion.text);
    inputRef.current?.focus();
  }, []);

  // Handle history item click
  const handleHistoryClick = useCallback((item: QueryHistoryItem) => {
    setNaturalQuery(item.naturalLanguage);
    setGeneratedSql(item.generatedSql);
    setShowHistory(false);
  }, []);

  // Handle form submit
  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    handleGenerateSql();
  }, [handleGenerateSql]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-hidden bg-background flex flex-col">
        {/* Header */}
        <div className="border-b border-border p-6">
          <div className="flex items-center justify-between max-w-6xl mx-auto">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">Natural Language Query</h1>
              <p className="text-foreground-secondary">
                Ask questions in plain English and get SQL queries instantly
              </p>
            </div>
            {session?.data_loaded && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition-colors ${
                    showHistory
                      ? 'border-brand-500 bg-brand-600/10 text-brand-500'
                      : 'border-border hover:bg-surface-hover text-foreground'
                  }`}
                >
                  <History className="w-4 h-4" />
                  History
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="px-6 pt-4 max-w-6xl mx-auto w-full">
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-500 flex-1">{error}</p>
              <button onClick={() => setError(null)} className="p-1 hover:bg-red-500/20 rounded">
                <X className="w-4 h-4 text-red-500" />
              </button>
            </div>
          </div>
        )}

        {/* Main content */}
        {!session?.data_loaded ? (
          /* Upload prompt */
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 rounded-2xl bg-brand-600/10 flex items-center justify-center mx-auto mb-6">
                <Wand2 className="w-10 h-10 text-brand-500" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Natural Language Query</h2>
              <p className="text-foreground-muted mb-8">
                Upload your data to start asking questions in plain English. Our AI will convert your questions into SQL queries automatically.
              </p>

              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                className="hidden"
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center justify-center gap-2 w-full px-6 py-4 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Uploading... {uploadProgress}%
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload Data File
                  </>
                )}
              </button>

              <div className="mt-8 grid grid-cols-1 gap-3">
                <div className="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border text-left">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <MessageSquare className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Natural Language</p>
                    <p className="text-xs text-foreground-muted">Ask in plain English</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-surface rounded-lg border border-border text-left">
                  <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                    <Zap className="w-5 h-5 text-blue-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-foreground">Instant SQL</p>
                    <p className="text-xs text-foreground-muted">AI generates optimized queries</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Query interface */
          <div className="flex-1 overflow-hidden flex">
            {/* Main query area */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Data source info */}
              <div className="px-6 py-3 bg-surface-muted border-b border-border">
                <div className="flex items-center gap-3 max-w-6xl mx-auto">
                  <FileSpreadsheet className="w-5 h-5 text-emerald-500" />
                  <span className="text-sm text-foreground font-medium">{session.file_name}</span>
                  <span className="text-sm text-foreground-muted">
                    ({session.row_count?.toLocaleString()} rows, {session.column_count} columns)
                  </span>
                </div>
              </div>

              {/* Query input */}
              <div className="px-6 py-4 border-b border-border">
                <form onSubmit={handleSubmit} className="max-w-6xl mx-auto">
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground-muted" />
                    <input
                      ref={inputRef}
                      type="text"
                      value={naturalQuery}
                      onChange={(e) => setNaturalQuery(e.target.value)}
                      placeholder="Ask a question about your data in plain English..."
                      className="w-full pl-12 pr-32 py-4 bg-surface border border-border rounded-xl text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 focus:border-brand-600"
                    />
                    <button
                      type="submit"
                      disabled={isGenerating || !naturalQuery.trim()}
                      className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                      {isGenerating ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Send className="w-4 h-4" />
                      )}
                      Generate
                    </button>
                  </div>
                </form>
              </div>

              {/* Suggestions */}
              {!generatedSql && !result && (
                <div className="px-6 py-4 border-b border-border">
                  <div className="max-w-6xl mx-auto">
                    <h3 className="text-sm font-medium text-foreground-muted mb-3">
                      Try asking:
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {QUERY_SUGGESTIONS.slice(0, 6).map((suggestion, idx) => (
                        <SuggestionChip
                          key={idx}
                          suggestion={suggestion}
                          onClick={() => handleSuggestionClick(suggestion)}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Results area */}
              <div className="flex-1 overflow-auto p-6">
                <div className="max-w-6xl mx-auto space-y-6">
                  {/* SQL Editor */}
                  {generatedSql && (
                    <SqlEditor
                      sql={generatedSql}
                      onChange={setGeneratedSql}
                      onRun={handleRunSql}
                      isRunning={isRunning}
                      isEditing={isEditing}
                      onEditToggle={() => setIsEditing(!isEditing)}
                      tableName={tableName}
                      explanation={sqlExplanation}
                    />
                  )}

                  {/* Results Table */}
                  <div className="bg-surface border border-border rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-foreground mb-4">Results</h3>
                    <ResultsTable result={result} isLoading={isRunning} />
                  </div>
                </div>
              </div>
            </div>

            {/* History sidebar */}
            <AnimatePresence>
              {showHistory && (
                <motion.div
                  initial={{ width: 0, opacity: 0 }}
                  animate={{ width: 320, opacity: 1 }}
                  exit={{ width: 0, opacity: 0 }}
                  className="border-l border-border bg-surface-muted overflow-hidden"
                >
                  <div className="w-80 h-full flex flex-col">
                    <div className="p-4 border-b border-border">
                      <h3 className="font-semibold text-foreground">Query History</h3>
                      <p className="text-xs text-foreground-muted mt-1">
                        {queryHistory.length} recent queries
                      </p>
                    </div>
                    <div className="flex-1 overflow-y-auto p-4 space-y-2">
                      {queryHistory.length === 0 ? (
                        <div className="text-center py-8">
                          <History className="w-8 h-8 text-foreground-muted mx-auto mb-2 opacity-50" />
                          <p className="text-sm text-foreground-muted">No queries yet</p>
                        </div>
                      ) : (
                        queryHistory.map((item) => (
                          <HistoryItem
                            key={item.id}
                            item={item}
                            onClick={() => handleHistoryClick(item)}
                          />
                        ))
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </main>
    </div>
  );
}
