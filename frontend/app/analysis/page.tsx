/**
 * ============================================================================
 * 📊 ANALYSIS WORKSPACE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Advanced data analysis workspace with:
 * - Data profiling and quality assessment
 * - Statistical analysis tools
 * - Forecasting with multiple methods
 * - AI-powered insights
 * - Interactive visualizations
 */

'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import {
  api,
  DataProfile,
  ForecastResult,
  StatisticalResult,
  InsightResult,
  AnalysisSession,
} from '@/lib/api/client';
import {
  Upload,
  FileSpreadsheet,
  BarChart3,
  TrendingUp,
  Brain,
  Loader2,
  X,
  CheckCircle2,
  AlertCircle,
  ChevronRight,
  Play,
  Settings,
  Download,
  RefreshCw,
  Table,
  PieChart,
  LineChart,
  Calculator,
  Lightbulb,
  Target,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  Info,
  Sparkles,
  FlaskConical,
  Activity,
  Layers,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

type AnalysisTab = 'overview' | 'profile' | 'statistics' | 'forecast' | 'insights';

interface ColumnInfo {
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
}

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const StatCard: React.FC<{
  label: string;
  value: string | number;
  icon?: React.ElementType;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  className?: string;
}> = ({ label, value, icon: Icon, trend, trendValue, className = '' }) => (
  <div className={`bg-surface rounded-xl border border-border p-4 ${className}`}>
    <div className="flex items-center justify-between mb-2">
      <span className="text-sm text-foreground-muted">{label}</span>
      {Icon && (
        <div className="w-8 h-8 rounded-lg bg-brand-600/10 flex items-center justify-center">
          <Icon className="w-4 h-4 text-brand-500" />
        </div>
      )}
    </div>
    <div className="flex items-end gap-2">
      <span className="text-2xl font-bold text-foreground">{value}</span>
      {trend && trendValue && (
        <span
          className={`flex items-center text-sm font-medium ${
            trend === 'up'
              ? 'text-emerald-500'
              : trend === 'down'
              ? 'text-red-500'
              : 'text-foreground-muted'
          }`}
        >
          {trend === 'up' && <ArrowUpRight className="w-4 h-4" />}
          {trend === 'down' && <ArrowDownRight className="w-4 h-4" />}
          {trend === 'neutral' && <Minus className="w-4 h-4" />}
          {trendValue}
        </span>
      )}
    </div>
  </div>
);

const QualityBadge: React.FC<{ level: string; score: number }> = ({ level, score }) => {
  const colors: Record<string, string> = {
    Excellent: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
    Good: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
    Fair: 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    Poor: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
    Critical: 'bg-red-500/10 text-red-500 border-red-500/20',
  };

  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-full border ${colors[level] || colors.Fair}`}>
      <CheckCircle2 className="w-4 h-4" />
      <span className="font-medium">{level}</span>
      <span className="text-sm opacity-75">({score}%)</span>
    </div>
  );
};

// =============================================================================
// UPLOAD SECTION
// =============================================================================

interface UploadSectionProps {
  onFileUpload: (file: File) => void;
  isUploading: boolean;
  uploadProgress: number;
}

const UploadSection: React.FC<UploadSectionProps> = ({
  onFileUpload,
  isUploading,
  uploadProgress,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFileUpload(file);
  };

  return (
    <div className="flex flex-col items-center justify-center py-16">
      <div className="w-20 h-20 rounded-2xl bg-brand-600/10 flex items-center justify-center mb-6">
        <BarChart3 className="w-10 h-10 text-brand-500" />
      </div>
      <h2 className="text-2xl font-bold text-foreground mb-2">Analysis Workspace</h2>
      <p className="text-foreground-muted mb-8 text-center max-w-md">
        Upload your data to get started with profiling, statistical analysis,
        forecasting, and AI-powered insights.
      </p>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`
          relative w-full max-w-lg border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer
          ${isDragging
            ? 'border-brand-500 bg-brand-600/5'
            : 'border-border hover:border-brand-500/50 hover:bg-surface-hover'
          }
          ${isUploading ? 'pointer-events-none' : ''}
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls,.json,.pdf,.txt"
          onChange={(e) => e.target.files?.[0] && onFileUpload(e.target.files[0])}
          className="hidden"
        />

        {isUploading ? (
          <div className="space-y-4">
            <Loader2 className="w-12 h-12 text-brand-500 mx-auto animate-spin" />
            <div>
              <p className="text-sm font-medium text-foreground mb-2">Processing your data...</p>
              <div className="w-full h-2 bg-surface-muted rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-600 transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-foreground-muted mt-2">{uploadProgress}% complete</p>
            </div>
          </div>
        ) : (
          <>
            <Upload className="w-12 h-12 text-brand-500 mx-auto mb-4" />
            <p className="text-foreground font-medium mb-1">
              Drop your data file here or click to browse
            </p>
            <p className="text-sm text-foreground-muted">
              Supports CSV, Excel, JSON, PDF, and text files
            </p>
          </>
        )}
      </div>

      {/* Quick start suggestions */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl w-full">
        {[
          { icon: TrendingUp, title: 'Forecast Sales', desc: 'Predict future trends' },
          { icon: FlaskConical, title: 'Run Statistics', desc: 'Hypothesis testing' },
          { icon: Lightbulb, title: 'Get Insights', desc: 'AI-powered analysis' },
        ].map((item) => (
          <div
            key={item.title}
            className="flex items-center gap-3 p-4 bg-surface rounded-xl border border-border"
          >
            <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center">
              <item.icon className="w-5 h-5 text-brand-500" />
            </div>
            <div>
              <p className="font-medium text-foreground text-sm">{item.title}</p>
              <p className="text-xs text-foreground-muted">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// =============================================================================
// DATA OVERVIEW TAB
// =============================================================================

interface DataOverviewProps {
  session: AnalysisSession;
  profile: DataProfile | null;
  insights: InsightResult[];
  onRefresh: () => void;
}

const DataOverview: React.FC<DataOverviewProps> = ({ session, profile, insights, onRefresh }) => (
  <div className="space-y-6">
    {/* Stats Grid */}
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard
        label="Rows"
        value={session.row_count?.toLocaleString() || '0'}
        icon={Table}
      />
      <StatCard
        label="Columns"
        value={session.column_count || 0}
        icon={Layers}
      />
      <StatCard
        label="Data Quality"
        value={profile?.quality_level || 'N/A'}
        icon={CheckCircle2}
      />
      <StatCard
        label="Quality Score"
        value={`${profile?.quality_score || 0}%`}
        icon={Target}
      />
    </div>

    {/* File Info */}
    <div className="bg-surface rounded-xl border border-border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-foreground">Data Source</h3>
        <button
          onClick={onRefresh}
          className="p-2 hover:bg-surface-hover rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className="w-4 h-4 text-foreground-muted" />
        </button>
      </div>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-xl bg-emerald-500/10 flex items-center justify-center">
          <FileSpreadsheet className="w-6 h-6 text-emerald-500" />
        </div>
        <div>
          <p className="font-medium text-foreground">{session.file_name || 'Unknown file'}</p>
          <p className="text-sm text-foreground-muted">
            {session.row_count?.toLocaleString()} rows &times; {session.column_count} columns
          </p>
        </div>
        {profile && (
          <div className="ml-auto">
            <QualityBadge level={profile.quality_level} score={profile.quality_score} />
          </div>
        )}
      </div>
    </div>

    {/* AI Summary */}
    {profile?.summary && (
      <div className="bg-gradient-to-br from-brand-600/10 to-brand-500/5 rounded-xl border border-brand-500/20 p-6">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-brand-500" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground mb-2">AI Summary</h3>
            <p className="text-foreground-secondary">{profile.summary}</p>
          </div>
        </div>
      </div>
    )}

    {/* Quick Insights */}
    {insights.length > 0 && (
      <div className="bg-surface rounded-xl border border-border p-6">
        <h3 className="text-lg font-semibold text-foreground mb-4">Key Insights</h3>
        <div className="space-y-3">
          {insights.slice(0, 5).map((insight, index) => (
            <div
              key={index}
              className={`flex items-start gap-3 p-3 rounded-lg ${
                insight.priority === 'Critical'
                  ? 'bg-red-500/10'
                  : insight.priority === 'High'
                  ? 'bg-amber-500/10'
                  : 'bg-surface-muted'
              }`}
            >
              <Lightbulb
                className={`w-5 h-5 flex-shrink-0 ${
                  insight.priority === 'Critical'
                    ? 'text-red-500'
                    : insight.priority === 'High'
                    ? 'text-amber-500'
                    : 'text-brand-500'
                }`}
              />
              <div>
                <p className="font-medium text-foreground">{insight.title}</p>
                <p className="text-sm text-foreground-muted">{insight.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    )}
  </div>
);

// =============================================================================
// DATA PROFILE TAB
// =============================================================================

interface DataProfileTabProps {
  profile: DataProfile | null;
  isLoading: boolean;
}

const DataProfileTab: React.FC<DataProfileTabProps> = ({ profile, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-16">
        <AlertCircle className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
        <p className="text-foreground-muted">No profile data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Column Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {profile.columns.map((col) => (
          <div
            key={col.name}
            className="bg-surface rounded-xl border border-border p-4 hover:border-brand-500/50 transition-colors"
          >
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-medium text-foreground truncate" title={col.name}>
                {col.name}
              </h4>
              <span className="px-2 py-0.5 text-xs font-medium bg-brand-600/10 text-brand-500 rounded">
                {col.semantic_type}
              </span>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-foreground-muted">Type</span>
                <span className="text-foreground">{col.type}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-foreground-muted">Unique</span>
                <span className="text-foreground">{col.unique_count.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-foreground-muted">Missing</span>
                <span className={col.missing_percentage > 10 ? 'text-amber-500' : 'text-foreground'}>
                  {col.missing_percentage.toFixed(1)}%
                </span>
              </div>

              {col.statistics && (
                <>
                  <div className="h-px bg-border my-2" />
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {col.statistics.min !== undefined && (
                      <div>
                        <span className="text-foreground-muted">Min: </span>
                        <span className="text-foreground">{col.statistics.min.toLocaleString()}</span>
                      </div>
                    )}
                    {col.statistics.max !== undefined && (
                      <div>
                        <span className="text-foreground-muted">Max: </span>
                        <span className="text-foreground">{col.statistics.max.toLocaleString()}</span>
                      </div>
                    )}
                    {col.statistics.mean !== undefined && (
                      <div>
                        <span className="text-foreground-muted">Mean: </span>
                        <span className="text-foreground">{col.statistics.mean.toFixed(2)}</span>
                      </div>
                    )}
                    {col.statistics.std !== undefined && (
                      <div>
                        <span className="text-foreground-muted">Std: </span>
                        <span className="text-foreground">{col.statistics.std.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// =============================================================================
// STATISTICS TAB
// =============================================================================

interface StatisticsTabProps {
  sessionId: string;
  columns: ColumnInfo[];
}

const StatisticsTab: React.FC<StatisticsTabProps> = ({ sessionId, columns }) => {
  const [selectedTest, setSelectedTest] = useState<string>('correlation');
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [result, setResult] = useState<StatisticalResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numericColumns = columns.filter(
    (c) => c.type === 'int64' || c.type === 'float64' || c.semantic_type.includes('numeric')
  );

  const tests = [
    { id: 'correlation', name: 'Correlation Analysis', desc: 'Measure relationship strength', minCols: 2 },
    { id: 't_test', name: 'T-Test', desc: 'Compare two group means', minCols: 2 },
    { id: 'anova', name: 'ANOVA', desc: 'Compare multiple groups', minCols: 2 },
    { id: 'chi_square', name: 'Chi-Square', desc: 'Test independence', minCols: 2 },
    { id: 'regression', name: 'Linear Regression', desc: 'Predict relationships', minCols: 2 },
  ];

  const runTest = async () => {
    if (selectedColumns.length < 2) {
      setError('Please select at least 2 columns');
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      const res = await api.session.runStatistics(sessionId, selectedTest, selectedColumns);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run test');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Test Selection */}
      <div className="lg:col-span-1 space-y-4">
        <div className="bg-surface rounded-xl border border-border p-4">
          <h3 className="font-semibold text-foreground mb-4">Statistical Tests</h3>
          <div className="space-y-2">
            {tests.map((test) => (
              <button
                key={test.id}
                onClick={() => setSelectedTest(test.id)}
                className={`w-full text-left p-3 rounded-lg transition-colors ${
                  selectedTest === test.id
                    ? 'bg-brand-600/10 border border-brand-500'
                    : 'hover:bg-surface-hover border border-transparent'
                }`}
              >
                <p className="font-medium text-foreground">{test.name}</p>
                <p className="text-xs text-foreground-muted">{test.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Column Selection */}
        <div className="bg-surface rounded-xl border border-border p-4">
          <h3 className="font-semibold text-foreground mb-4">Select Columns</h3>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {numericColumns.map((col) => (
              <label
                key={col.name}
                className="flex items-center gap-3 p-2 rounded-lg hover:bg-surface-hover cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedColumns.includes(col.name)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedColumns([...selectedColumns, col.name]);
                    } else {
                      setSelectedColumns(selectedColumns.filter((c) => c !== col.name));
                    }
                  }}
                  className="w-4 h-4 accent-brand-600"
                />
                <span className="text-sm text-foreground">{col.name}</span>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={runTest}
          disabled={isRunning || selectedColumns.length < 2}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="w-4 h-4" />
              Run Analysis
            </>
          )}
        </button>
      </div>

      {/* Results */}
      <div className="lg:col-span-2">
        {error && (
          <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-sm text-red-500">{error}</p>
          </div>
        )}

        {result ? (
          <div className="bg-surface rounded-xl border border-border p-6">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-foreground">Results</h3>
              <span
                className={`px-3 py-1 rounded-full text-sm font-medium ${
                  result.significant
                    ? 'bg-emerald-500/10 text-emerald-500'
                    : 'bg-foreground-muted/10 text-foreground-muted'
                }`}
              >
                {result.significant ? 'Significant' : 'Not Significant'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 bg-surface-muted rounded-lg">
                <p className="text-sm text-foreground-muted mb-1">Test Statistic</p>
                <p className="text-2xl font-bold text-foreground">
                  {result.test_statistic.toFixed(4)}
                </p>
              </div>
              <div className="p-4 bg-surface-muted rounded-lg">
                <p className="text-sm text-foreground-muted mb-1">P-Value</p>
                <p className="text-2xl font-bold text-foreground">
                  {result.p_value < 0.0001 ? '< 0.0001' : result.p_value.toFixed(4)}
                </p>
              </div>
              {result.effect_size !== undefined && (
                <div className="p-4 bg-surface-muted rounded-lg">
                  <p className="text-sm text-foreground-muted mb-1">Effect Size</p>
                  <p className="text-2xl font-bold text-foreground">
                    {result.effect_size.toFixed(4)}
                  </p>
                </div>
              )}
              {result.confidence_interval && (
                <div className="p-4 bg-surface-muted rounded-lg">
                  <p className="text-sm text-foreground-muted mb-1">95% CI</p>
                  <p className="text-lg font-bold text-foreground">
                    [{result.confidence_interval[0].toFixed(2)}, {result.confidence_interval[1].toFixed(2)}]
                  </p>
                </div>
              )}
            </div>

            <div className="p-4 bg-brand-600/5 border border-brand-500/20 rounded-lg">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-brand-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-medium text-foreground mb-1">Interpretation</p>
                  <p className="text-sm text-foreground-secondary">{result.interpretation}</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-surface rounded-xl border border-border p-12 text-center">
            <Calculator className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
            <p className="text-foreground-muted">
              Select columns and run a statistical test to see results
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// FORECAST TAB
// =============================================================================

interface ForecastTabProps {
  sessionId: string;
  columns: ColumnInfo[];
}

const ForecastTab: React.FC<ForecastTabProps> = ({ sessionId, columns }) => {
  const [selectedColumn, setSelectedColumn] = useState<string>('');
  const [periods, setPeriods] = useState(12);
  const [method, setMethod] = useState<string>('auto');
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const numericColumns = columns.filter(
    (c) => c.type === 'int64' || c.type === 'float64'
  );

  const methods = [
    { id: 'auto', name: 'Auto-Select', desc: 'Best method for your data' },
    { id: 'moving_average', name: 'Moving Average', desc: 'Simple trend smoothing' },
    { id: 'exponential', name: 'Exponential Smoothing', desc: 'Weighted recent values' },
    { id: 'holt', name: 'Holt\'s Method', desc: 'Trend projection' },
    { id: 'holt_winters', name: 'Holt-Winters', desc: 'Seasonal patterns' },
    { id: 'linear', name: 'Linear Trend', desc: 'Straight line projection' },
  ];

  const runForecast = async () => {
    if (!selectedColumn) {
      setError('Please select a column to forecast');
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      const res = await api.session.forecast(sessionId, selectedColumn, periods, method);
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run forecast');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Configuration */}
      <div className="lg:col-span-1 space-y-4">
        {/* Column Selection */}
        <div className="bg-surface rounded-xl border border-border p-4">
          <h3 className="font-semibold text-foreground mb-4">Select Column</h3>
          <select
            value={selectedColumn}
            onChange={(e) => setSelectedColumn(e.target.value)}
            className="w-full px-3 py-2 bg-surface-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
          >
            <option value="">Choose a column...</option>
            {numericColumns.map((col) => (
              <option key={col.name} value={col.name}>
                {col.name}
              </option>
            ))}
          </select>
        </div>

        {/* Forecast Periods */}
        <div className="bg-surface rounded-xl border border-border p-4">
          <h3 className="font-semibold text-foreground mb-4">Forecast Periods</h3>
          <input
            type="number"
            value={periods}
            onChange={(e) => setPeriods(Math.max(1, parseInt(e.target.value) || 1))}
            min={1}
            max={365}
            className="w-full px-3 py-2 bg-surface-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
          />
          <p className="text-xs text-foreground-muted mt-2">
            Number of future periods to predict
          </p>
        </div>

        {/* Method Selection */}
        <div className="bg-surface rounded-xl border border-border p-4">
          <h3 className="font-semibold text-foreground mb-4">Forecasting Method</h3>
          <div className="space-y-2">
            {methods.map((m) => (
              <button
                key={m.id}
                onClick={() => setMethod(m.id)}
                className={`w-full text-left p-2 rounded-lg transition-colors ${
                  method === m.id
                    ? 'bg-brand-600/10 border border-brand-500'
                    : 'hover:bg-surface-hover border border-transparent'
                }`}
              >
                <p className="font-medium text-foreground text-sm">{m.name}</p>
                <p className="text-xs text-foreground-muted">{m.desc}</p>
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={runForecast}
          disabled={isRunning || !selectedColumn}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Forecasting...
            </>
          ) : (
            <>
              <TrendingUp className="w-4 h-4" />
              Generate Forecast
            </>
          )}
        </button>
      </div>

      {/* Results */}
      <div className="lg:col-span-2">
        {error && (
          <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <p className="text-sm text-red-500">{error}</p>
          </div>
        )}

        {result ? (
          <div className="space-y-4">
            {/* Metrics */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-surface rounded-xl border border-border p-4 text-center">
                <p className="text-sm text-foreground-muted mb-1">MAE</p>
                <p className="text-xl font-bold text-foreground">{result.metrics.mae.toFixed(2)}</p>
              </div>
              <div className="bg-surface rounded-xl border border-border p-4 text-center">
                <p className="text-sm text-foreground-muted mb-1">RMSE</p>
                <p className="text-xl font-bold text-foreground">{result.metrics.rmse.toFixed(2)}</p>
              </div>
              <div className="bg-surface rounded-xl border border-border p-4 text-center">
                <p className="text-sm text-foreground-muted mb-1">MAPE</p>
                <p className="text-xl font-bold text-foreground">{result.metrics.mape.toFixed(1)}%</p>
              </div>
            </div>

            {/* Info Cards */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-surface rounded-xl border border-border p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-brand-500" />
                  <span className="text-sm text-foreground-muted">Method Used</span>
                </div>
                <p className="font-medium text-foreground">{result.method}</p>
              </div>
              <div className="bg-surface rounded-xl border border-border p-4">
                <div className="flex items-center gap-2 mb-2">
                  <TrendingUp className="w-4 h-4 text-brand-500" />
                  <span className="text-sm text-foreground-muted">Trend Direction</span>
                </div>
                <p className="font-medium text-foreground capitalize">{result.trend_direction}</p>
              </div>
            </div>

            {/* Forecast Values Table */}
            <div className="bg-surface rounded-xl border border-border p-4">
              <h4 className="font-semibold text-foreground mb-4">Forecast Values</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 text-foreground-muted">Period</th>
                      <th className="text-right py-2 text-foreground-muted">Forecast</th>
                      <th className="text-right py-2 text-foreground-muted">Lower CI</th>
                      <th className="text-right py-2 text-foreground-muted">Upper CI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.forecast_values.slice(0, 10).map((val, idx) => (
                      <tr key={idx} className="border-b border-border/50">
                        <td className="py-2 text-foreground">
                          {result.forecast_dates?.[idx] || `Period ${idx + 1}`}
                        </td>
                        <td className="py-2 text-right font-medium text-foreground">
                          {val.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2 text-right text-foreground-muted">
                          {result.confidence_lower[idx]?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                        <td className="py-2 text-right text-foreground-muted">
                          {result.confidence_upper[idx]?.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {result.forecast_values.length > 10 && (
                <p className="text-xs text-foreground-muted mt-2 text-center">
                  Showing first 10 of {result.forecast_values.length} forecast periods
                </p>
              )}
            </div>
          </div>
        ) : (
          <div className="bg-surface rounded-xl border border-border p-12 text-center">
            <LineChart className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
            <p className="text-foreground-muted">
              Select a column and configure parameters to generate a forecast
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// INSIGHTS TAB
// =============================================================================

interface InsightsTabProps {
  insights: InsightResult[];
  isLoading: boolean;
  onRefresh: () => void;
}

const InsightsTab: React.FC<InsightsTabProps> = ({ insights, isLoading, onRefresh }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  const priorityColors: Record<string, string> = {
    Critical: 'border-red-500 bg-red-500/5',
    High: 'border-amber-500 bg-amber-500/5',
    Medium: 'border-blue-500 bg-blue-500/5',
    Low: 'border-foreground-muted bg-surface-muted',
    Info: 'border-border bg-surface',
  };

  const typeIcons: Record<string, React.ElementType> = {
    Trend: TrendingUp,
    Anomaly: AlertCircle,
    Comparison: BarChart3,
    Distribution: PieChart,
    Correlation: Activity,
    Summary: FileSpreadsheet,
    Forecast: LineChart,
    Recommendation: Lightbulb,
    Warning: AlertCircle,
    Achievement: Target,
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-foreground">AI-Generated Insights</h3>
        <button
          onClick={onRefresh}
          className="flex items-center gap-2 px-3 py-1.5 hover:bg-surface-hover rounded-lg transition-colors text-sm"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {insights.length === 0 ? (
        <div className="text-center py-16">
          <Brain className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
          <p className="text-foreground-muted">No insights generated yet</p>
          <button
            onClick={onRefresh}
            className="mt-4 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors"
          >
            Generate Insights
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {insights.map((insight, index) => {
            const Icon = typeIcons[insight.type] || Lightbulb;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
                className={`border-l-4 rounded-xl p-5 ${priorityColors[insight.priority] || priorityColors.Info}`}
              >
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center flex-shrink-0">
                    <Icon className="w-5 h-5 text-brand-500" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold text-foreground">{insight.title}</h4>
                      <span className="px-2 py-0.5 text-xs font-medium bg-surface-muted rounded">
                        {insight.type}
                      </span>
                      <span className="px-2 py-0.5 text-xs font-medium bg-surface-muted rounded">
                        {insight.priority}
                      </span>
                    </div>
                    <p className="text-foreground-secondary mb-3">{insight.description}</p>

                    {insight.recommendation && (
                      <div className="p-3 bg-brand-600/5 border border-brand-500/20 rounded-lg">
                        <p className="text-sm text-foreground">
                          <span className="font-medium">Recommendation:</span> {insight.recommendation}
                        </p>
                      </div>
                    )}

                    {(insight.metric || insight.value !== undefined) && (
                      <div className="flex items-center gap-4 mt-3">
                        {insight.metric && (
                          <span className="text-sm text-foreground-muted">
                            Metric: <span className="text-foreground">{insight.metric}</span>
                          </span>
                        )}
                        {insight.value !== undefined && (
                          <span className="text-sm text-foreground-muted">
                            Value: <span className="font-medium text-foreground">{insight.value}</span>
                          </span>
                        )}
                        {insight.change !== undefined && (
                          <span
                            className={`text-sm font-medium ${
                              insight.change > 0 ? 'text-emerald-500' : insight.change < 0 ? 'text-red-500' : ''
                            }`}
                          >
                            {insight.change > 0 ? '+' : ''}
                            {insight.change}%
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// =============================================================================
// MAIN ANALYSIS PAGE
// =============================================================================

export default function AnalysisPage() {
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [profile, setProfile] = useState<DataProfile | null>(null);
  const [insights, setInsights] = useState<InsightResult[]>([]);
  const [activeTab, setActiveTab] = useState<AnalysisTab>('overview');

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isLoadingProfile, setIsLoadingProfile] = useState(false);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create session on mount - auto-loads active dataset if available
  useEffect(() => {
    const initSession = async () => {
      try {
        const newSession = await api.session.create();
        setSession(newSession);

        // Show notification if data was auto-loaded from active dataset
        if (newSession.data_loaded && newSession.file_name) {
          console.log(`📊 Auto-loaded active dataset: ${newSession.file_name}`);
        }
      } catch (err) {
        console.error('Failed to create session:', err);
        setError('Failed to initialize analysis session');
      }
    };
    initSession();
  }, []);

  // Load profile
  const loadProfile = useCallback(async () => {
    if (!session?.id || !session.data_loaded) return;

    setIsLoadingProfile(true);
    try {
      const profileData = await api.session.getProfile(session.id);
      setProfile(profileData);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setIsLoadingProfile(false);
    }
  }, [session?.id, session?.data_loaded]);

  // Load insights
  const loadInsights = useCallback(async () => {
    if (!session?.id || !session.data_loaded) return;

    setIsLoadingInsights(true);
    try {
      const insightsData = await api.session.getInsights(session.id);
      setInsights(insightsData);
    } catch (err) {
      console.error('Failed to load insights:', err);
    } finally {
      setIsLoadingInsights(false);
    }
  }, [session?.id, session?.data_loaded]);

  // Load data when session has data
  useEffect(() => {
    if (session?.data_loaded) {
      loadProfile();
      loadInsights();
    }
  }, [session?.data_loaded, loadProfile, loadInsights]);

  // Handle file upload
  const handleFileUpload = useCallback(
    async (file: File) => {
      if (!session?.id) return;

      setIsUploading(true);
      setUploadProgress(0);
      setError(null);

      try {
        const result = await api.session.uploadFile(session.id, file, (progress) => {
          setUploadProgress(progress);
        });

        setSession({
          ...session,
          data_loaded: true,
          file_name: result.file_name,
          row_count: result.rows,
          column_count: result.columns,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Upload failed');
      } finally {
        setIsUploading(false);
        setUploadProgress(0);
      }
    },
    [session]
  );

  const tabs: { id: AnalysisTab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'profile', label: 'Data Profile', icon: Table },
    { id: 'statistics', label: 'Statistics', icon: Calculator },
    { id: 'forecast', label: 'Forecast', icon: TrendingUp },
    { id: 'insights', label: 'Insights', icon: Lightbulb },
  ];

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-auto bg-background">
        <div className="max-w-7xl mx-auto p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Analysis Workspace</h1>
            <p className="text-foreground-secondary">
              Advanced data profiling, statistical analysis, and AI-powered insights
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-500">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto p-1 hover:bg-red-500/20 rounded"
              >
                <X className="w-4 h-4 text-red-500" />
              </button>
            </div>
          )}

          {/* Main Content */}
          {!session?.data_loaded ? (
            <UploadSection
              onFileUpload={handleFileUpload}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
            />
          ) : (
            <>
              {/* Active Dataset Info */}
              <div className="mb-6 p-4 bg-brand-500/5 border border-brand-500/20 rounded-xl flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-brand-500/20 flex items-center justify-center">
                    <FileSpreadsheet className="w-5 h-5 text-brand-500" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">{session.file_name}</p>
                    <p className="text-sm text-foreground-muted">
                      {session.row_count?.toLocaleString()} rows · {session.column_count} columns
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    // Reset session to allow new upload
                    setSession(prev => prev ? { ...prev, data_loaded: false, file_name: undefined } : null);
                    setProfile(null);
                    setInsights(null);
                  }}
                  className="px-4 py-2 text-sm font-medium text-brand-500 hover:bg-brand-500/10 rounded-lg transition-colors"
                >
                  Change Dataset
                </button>
              </div>

              {/* Tabs */}
              <div className="flex items-center gap-1 mb-6 p-1 bg-surface-muted rounded-xl">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium text-sm transition-colors ${
                      activeTab === tab.id
                        ? 'bg-surface text-foreground shadow-sm'
                        : 'text-foreground-muted hover:text-foreground'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeTab}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {activeTab === 'overview' && (
                    <DataOverview
                      session={session}
                      profile={profile}
                      insights={insights}
                      onRefresh={() => {
                        loadProfile();
                        loadInsights();
                      }}
                    />
                  )}
                  {activeTab === 'profile' && (
                    <DataProfileTab profile={profile} isLoading={isLoadingProfile} />
                  )}
                  {activeTab === 'statistics' && session?.id && (
                    <StatisticsTab
                      sessionId={session.id}
                      columns={profile?.columns || []}
                    />
                  )}
                  {activeTab === 'forecast' && session?.id && (
                    <ForecastTab
                      sessionId={session.id}
                      columns={profile?.columns || []}
                    />
                  )}
                  {activeTab === 'insights' && (
                    <InsightsTab
                      insights={insights}
                      isLoading={isLoadingInsights}
                      onRefresh={loadInsights}
                    />
                  )}
                </motion.div>
              </AnimatePresence>
            </>
          )}
        </div>
      </main>
    </div>
  );
}
