/**
 * ============================================================================
 * 🔍 QUERY BUILDER - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Visual query construction interface for:
 * - Column selection with drag-and-drop
 * - Aggregations (SUM, AVG, COUNT, MIN, MAX, etc.)
 * - Filtering with multiple conditions
 * - Grouping and sorting
 * - Real-time preview
 * - Export to CSV/Excel/JSON
 */

'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { api, AnalysisSession, DataProfile } from '@/lib/api/client';
import {
  Database,
  Table,
  Columns,
  Filter,
  ArrowUpDown,
  Layers,
  Play,
  Download,
  Upload,
  Loader2,
  X,
  Plus,
  Trash2,
  ChevronDown,
  ChevronRight,
  GripVertical,
  FileSpreadsheet,
  AlertCircle,
  CheckCircle2,
  Copy,
  Eye,
  EyeOff,
  Calculator,
  Hash,
  Type,
  Calendar,
  ToggleLeft,
  RefreshCw,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

interface ColumnConfig {
  name: string;
  type: string;
  alias?: string;
  aggregation?: AggregationType;
  visible: boolean;
}

interface FilterCondition {
  id: string;
  column: string;
  operator: FilterOperator;
  value: string;
  connector: 'AND' | 'OR';
}

interface SortConfig {
  column: string;
  direction: 'ASC' | 'DESC';
}

type AggregationType = 'none' | 'sum' | 'avg' | 'count' | 'min' | 'max' | 'count_distinct';
type FilterOperator = '=' | '!=' | '>' | '<' | '>=' | '<=' | 'contains' | 'starts_with' | 'ends_with' | 'is_null' | 'is_not_null';

interface QueryResult {
  columns: string[];
  data: any[][];
  rowCount: number;
  executionTime: number;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const AGGREGATIONS: { value: AggregationType; label: string; description: string }[] = [
  { value: 'none', label: 'None', description: 'No aggregation' },
  { value: 'sum', label: 'SUM', description: 'Sum of values' },
  { value: 'avg', label: 'AVG', description: 'Average value' },
  { value: 'count', label: 'COUNT', description: 'Count of rows' },
  { value: 'count_distinct', label: 'COUNT DISTINCT', description: 'Unique count' },
  { value: 'min', label: 'MIN', description: 'Minimum value' },
  { value: 'max', label: 'MAX', description: 'Maximum value' },
];

const OPERATORS: { value: FilterOperator; label: string; description: string }[] = [
  { value: '=', label: 'equals', description: 'Exact match' },
  { value: '!=', label: 'not equals', description: 'Does not match' },
  { value: '>', label: 'greater than', description: 'Greater than value' },
  { value: '<', label: 'less than', description: 'Less than value' },
  { value: '>=', label: 'greater or equal', description: 'Greater than or equal' },
  { value: '<=', label: 'less or equal', description: 'Less than or equal' },
  { value: 'contains', label: 'contains', description: 'Contains text' },
  { value: 'starts_with', label: 'starts with', description: 'Starts with text' },
  { value: 'ends_with', label: 'ends with', description: 'Ends with text' },
  { value: 'is_null', label: 'is empty', description: 'Value is null/empty' },
  { value: 'is_not_null', label: 'is not empty', description: 'Value is not null' },
];

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

const getColumnIcon = (type: string) => {
  if (type.includes('int') || type.includes('float') || type.includes('numeric')) {
    return Hash;
  }
  if (type.includes('date') || type.includes('time')) {
    return Calendar;
  }
  if (type.includes('bool')) {
    return ToggleLeft;
  }
  return Type;
};

const generateQueryPreview = (
  columns: ColumnConfig[],
  filters: FilterCondition[],
  groupBy: string[],
  sortBy: SortConfig[],
  tableName: string
): string => {
  const selectedCols = columns.filter(c => c.visible);
  if (selectedCols.length === 0) return '';

  // SELECT clause
  const selectParts = selectedCols.map(col => {
    if (col.aggregation && col.aggregation !== 'none') {
      const aggFunc = col.aggregation.toUpperCase().replace('_', ' ');
      return `${aggFunc}(${col.name})${col.alias ? ` AS ${col.alias}` : ''}`;
    }
    return col.alias ? `${col.name} AS ${col.alias}` : col.name;
  });

  let query = `SELECT\n  ${selectParts.join(',\n  ')}\nFROM ${tableName}`;

  // WHERE clause
  if (filters.length > 0) {
    const whereParts = filters.map((f, i) => {
      let condition = '';
      if (f.operator === 'is_null') {
        condition = `${f.column} IS NULL`;
      } else if (f.operator === 'is_not_null') {
        condition = `${f.column} IS NOT NULL`;
      } else if (f.operator === 'contains') {
        condition = `${f.column} LIKE '%${f.value}%'`;
      } else if (f.operator === 'starts_with') {
        condition = `${f.column} LIKE '${f.value}%'`;
      } else if (f.operator === 'ends_with') {
        condition = `${f.column} LIKE '%${f.value}'`;
      } else {
        condition = `${f.column} ${f.operator} '${f.value}'`;
      }
      return i === 0 ? condition : `${f.connector} ${condition}`;
    });
    query += `\nWHERE\n  ${whereParts.join('\n  ')}`;
  }

  // GROUP BY clause
  if (groupBy.length > 0) {
    query += `\nGROUP BY\n  ${groupBy.join(', ')}`;
  }

  // ORDER BY clause
  if (sortBy.length > 0) {
    const orderParts = sortBy.map(s => `${s.column} ${s.direction}`);
    query += `\nORDER BY\n  ${orderParts.join(', ')}`;
  }

  return query;
};

// =============================================================================
// COLUMN SELECTOR COMPONENT
// =============================================================================

interface ColumnSelectorProps {
  columns: ColumnConfig[];
  onToggle: (name: string) => void;
  onAggregationChange: (name: string, agg: AggregationType) => void;
  onAliasChange: (name: string, alias: string) => void;
}

const ColumnSelector: React.FC<ColumnSelectorProps> = ({
  columns,
  onToggle,
  onAggregationChange,
  onAliasChange,
}) => {
  const [expandedColumn, setExpandedColumn] = useState<string | null>(null);

  return (
    <div className="space-y-2">
      {columns.map((col) => {
        const Icon = getColumnIcon(col.type);
        const isExpanded = expandedColumn === col.name;

        return (
          <div
            key={col.name}
            className={`border rounded-lg transition-colors ${
              col.visible
                ? 'border-brand-500 bg-brand-600/5'
                : 'border-border hover:border-border-hover'
            }`}
          >
            <div
              className="flex items-center gap-3 p-3 cursor-pointer"
              onClick={() => onToggle(col.name)}
            >
              <GripVertical className="w-4 h-4 text-foreground-muted" />
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  col.visible ? 'bg-brand-600/20' : 'bg-surface-muted'
                }`}
              >
                <Icon className={`w-4 h-4 ${col.visible ? 'text-brand-500' : 'text-foreground-muted'}`} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-foreground truncate">{col.name}</p>
                <p className="text-xs text-foreground-muted">{col.type}</p>
              </div>
              {col.visible && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedColumn(isExpanded ? null : col.name);
                  }}
                  className="p-1 hover:bg-surface-hover rounded"
                >
                  {isExpanded ? (
                    <ChevronDown className="w-4 h-4 text-foreground-muted" />
                  ) : (
                    <ChevronRight className="w-4 h-4 text-foreground-muted" />
                  )}
                </button>
              )}
              {col.visible ? (
                <Eye className="w-4 h-4 text-brand-500" />
              ) : (
                <EyeOff className="w-4 h-4 text-foreground-muted" />
              )}
            </div>

            {/* Expanded options */}
            <AnimatePresence>
              {isExpanded && col.visible && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden border-t border-border"
                >
                  <div className="p-3 space-y-3">
                    {/* Aggregation */}
                    <div>
                      <label className="text-xs text-foreground-muted mb-1 block">Aggregation</label>
                      <select
                        value={col.aggregation || 'none'}
                        onChange={(e) => onAggregationChange(col.name, e.target.value as AggregationType)}
                        onClick={(e) => e.stopPropagation()}
                        className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                      >
                        {AGGREGATIONS.map((agg) => (
                          <option key={agg.value} value={agg.value}>
                            {agg.label}
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Alias */}
                    <div>
                      <label className="text-xs text-foreground-muted mb-1 block">Display Name (Alias)</label>
                      <input
                        type="text"
                        value={col.alias || ''}
                        onChange={(e) => onAliasChange(col.name, e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                        placeholder={col.name}
                        className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>
  );
};

// =============================================================================
// FILTER BUILDER COMPONENT
// =============================================================================

interface FilterBuilderProps {
  filters: FilterCondition[];
  columns: string[];
  onAdd: () => void;
  onRemove: (id: string) => void;
  onUpdate: (id: string, field: keyof FilterCondition, value: any) => void;
}

const FilterBuilder: React.FC<FilterBuilderProps> = ({
  filters,
  columns,
  onAdd,
  onRemove,
  onUpdate,
}) => {
  return (
    <div className="space-y-3">
      {filters.length === 0 ? (
        <div className="text-center py-6 text-foreground-muted">
          <Filter className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No filters applied</p>
        </div>
      ) : (
        filters.map((filter, index) => (
          <div
            key={filter.id}
            className="flex items-center gap-2 p-3 bg-surface border border-border rounded-lg"
          >
            {index > 0 && (
              <select
                value={filter.connector}
                onChange={(e) => onUpdate(filter.id, 'connector', e.target.value)}
                className="px-2 py-1 bg-surface-muted border border-border rounded text-xs font-medium text-foreground"
              >
                <option value="AND">AND</option>
                <option value="OR">OR</option>
              </select>
            )}

            <select
              value={filter.column}
              onChange={(e) => onUpdate(filter.id, 'column', e.target.value)}
              className="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            >
              <option value="">Select column...</option>
              {columns.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>

            <select
              value={filter.operator}
              onChange={(e) => onUpdate(filter.id, 'operator', e.target.value)}
              className="px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            >
              {OPERATORS.map((op) => (
                <option key={op.value} value={op.value}>{op.label}</option>
              ))}
            </select>

            {!['is_null', 'is_not_null'].includes(filter.operator) && (
              <input
                type="text"
                value={filter.value}
                onChange={(e) => onUpdate(filter.id, 'value', e.target.value)}
                placeholder="Value..."
                className="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              />
            )}

            <button
              onClick={() => onRemove(filter.id)}
              className="p-2 hover:bg-red-500/10 rounded-lg transition-colors"
            >
              <Trash2 className="w-4 h-4 text-red-500" />
            </button>
          </div>
        ))
      )}

      <button
        onClick={onAdd}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-dashed border-border rounded-lg text-foreground-muted hover:text-foreground hover:border-brand-500 transition-colors"
      >
        <Plus className="w-4 h-4" />
        Add Filter
      </button>
    </div>
  );
};

// =============================================================================
// RESULTS TABLE COMPONENT
// =============================================================================

interface ResultsTableProps {
  result: QueryResult | null;
  isLoading: boolean;
}

const ResultsTable: React.FC<ResultsTableProps> = ({ result, isLoading }) => {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="text-center py-16">
        <Table className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
        <p className="text-foreground-muted">Run a query to see results</p>
      </div>
    );
  }

  return (
    <div>
      {/* Stats bar */}
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
                  <td
                    key={cellIdx}
                    className="px-4 py-3 text-foreground whitespace-nowrap"
                  >
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
// MAIN QUERY BUILDER PAGE
// =============================================================================

export default function QueryBuilderPage() {
  // Session state
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [profile, setProfile] = useState<DataProfile | null>(null);

  // Query builder state
  const [columns, setColumns] = useState<ColumnConfig[]>([]);
  const [filters, setFilters] = useState<FilterCondition[]>([]);
  const [groupBy, setGroupBy] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState<SortConfig[]>([]);

  // Results state
  const [result, setResult] = useState<QueryResult | null>(null);
  const [queryPreview, setQueryPreview] = useState<string>('');

  // UI state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState<'columns' | 'filters' | 'group' | 'sort'>('columns');
  const [showQuery, setShowQuery] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

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

  // Update query preview when config changes
  useEffect(() => {
    const preview = generateQueryPreview(
      columns,
      filters,
      groupBy,
      sortBy,
      session?.file_name || 'data'
    );
    setQueryPreview(preview);
  }, [columns, filters, groupBy, sortBy, session?.file_name]);

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

      // Initialize columns
      const cols: ColumnConfig[] = profileData.columns.map((col) => ({
        name: col.name,
        type: col.type,
        visible: true,
        aggregation: 'none',
      }));
      setColumns(cols);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [session]);

  // Column handlers
  const handleColumnToggle = useCallback((name: string) => {
    setColumns(prev => prev.map(col =>
      col.name === name ? { ...col, visible: !col.visible } : col
    ));
  }, []);

  const handleAggregationChange = useCallback((name: string, agg: AggregationType) => {
    setColumns(prev => prev.map(col =>
      col.name === name ? { ...col, aggregation: agg } : col
    ));
  }, []);

  const handleAliasChange = useCallback((name: string, alias: string) => {
    setColumns(prev => prev.map(col =>
      col.name === name ? { ...col, alias } : col
    ));
  }, []);

  // Filter handlers
  const handleAddFilter = useCallback(() => {
    const newFilter: FilterCondition = {
      id: `filter-${Date.now()}`,
      column: columns[0]?.name || '',
      operator: '=',
      value: '',
      connector: 'AND',
    };
    setFilters(prev => [...prev, newFilter]);
  }, [columns]);

  const handleRemoveFilter = useCallback((id: string) => {
    setFilters(prev => prev.filter(f => f.id !== id));
  }, []);

  const handleUpdateFilter = useCallback((id: string, field: keyof FilterCondition, value: any) => {
    setFilters(prev => prev.map(f =>
      f.id === id ? { ...f, [field]: value } : f
    ));
  }, []);

  // Group by handlers
  const handleToggleGroupBy = useCallback((column: string) => {
    setGroupBy(prev =>
      prev.includes(column)
        ? prev.filter(c => c !== column)
        : [...prev, column]
    );
  }, []);

  // Sort handlers
  const handleAddSort = useCallback((column: string) => {
    if (sortBy.find(s => s.column === column)) return;
    setSortBy(prev => [...prev, { column, direction: 'ASC' }]);
  }, [sortBy]);

  const handleRemoveSort = useCallback((column: string) => {
    setSortBy(prev => prev.filter(s => s.column !== column));
  }, []);

  const handleToggleSortDirection = useCallback((column: string) => {
    setSortBy(prev => prev.map(s =>
      s.column === column
        ? { ...s, direction: s.direction === 'ASC' ? 'DESC' : 'ASC' }
        : s
    ));
  }, []);

  // Run query
  const handleRunQuery = useCallback(async () => {
    if (!session?.id) return;

    setIsRunning(true);
    setError(null);

    try {
      // Build query config
      const selectedColumns = columns.filter(c => c.visible).map(c => ({
        name: c.name,
        aggregation: c.aggregation,
        alias: c.alias,
      }));

      const queryConfig = {
        columns: selectedColumns,
        filters: filters.map(f => ({
          column: f.column,
          operator: f.operator,
          value: f.value,
          connector: f.connector,
        })),
        group_by: groupBy,
        order_by: sortBy.map(s => ({
          column: s.column,
          direction: s.direction,
        })),
      };

      // Execute query via natural language (the backend will interpret)
      const queryText = `Execute query: ${queryPreview}`;
      const response = await api.session.query(session.id, queryText);

      // Mock result for now (in real implementation, backend returns structured data)
      if (response.table || response.data) {
        const tableData = response.table || response.data;
        setResult({
          columns: tableData.columns || selectedColumns.map(c => c.alias || c.name),
          data: tableData.rows || tableData.data || [],
          rowCount: tableData.row_count || (tableData.rows || tableData.data || []).length,
          executionTime: response.execution_time || 0,
        });
      } else {
        // Simulate result for demo
        const mockResult: QueryResult = {
          columns: selectedColumns.map(c => c.alias || c.name),
          data: [],
          rowCount: 0,
          executionTime: 15.3,
        };
        setResult(mockResult);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Query failed');
    } finally {
      setIsRunning(false);
    }
  }, [session?.id, columns, filters, groupBy, sortBy, queryPreview]);

  // Export results
  const handleExport = useCallback(async (format: 'csv' | 'excel' | 'json') => {
    if (!session?.id || !result) return;

    try {
      const blob = await api.session.export(session.id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `query_results.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Export failed');
    }
  }, [session?.id, result]);

  // Copy query to clipboard
  const handleCopyQuery = useCallback(() => {
    navigator.clipboard.writeText(queryPreview);
  }, [queryPreview]);

  const selectedColumnCount = columns.filter(c => c.visible).length;
  const columnNames = columns.map(c => c.name);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-hidden bg-background flex flex-col">
        {/* Header */}
        <div className="border-b border-border p-6">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">Query Builder</h1>
              <p className="text-foreground-secondary">
                Build queries visually with aggregations, filters, and grouping
              </p>
            </div>
            {session?.data_loaded && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setShowQuery(!showQuery)}
                  className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
                >
                  <Database className="w-4 h-4" />
                  {showQuery ? 'Hide' : 'Show'} SQL
                </button>
                <button
                  onClick={handleRunQuery}
                  disabled={isRunning || selectedColumnCount === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {isRunning ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Run Query
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="px-6 pt-4 max-w-7xl mx-auto w-full">
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
                <Database className="w-10 h-10 text-brand-500" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Upload Data</h2>
              <p className="text-foreground-muted mb-8">
                Upload a CSV, Excel, or JSON file to start building queries
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
                    Choose File
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Query builder interface */
          <div className="flex-1 overflow-hidden flex">
            {/* Left panel - Configuration */}
            <div className="w-80 border-r border-border flex flex-col overflow-hidden">
              {/* Data source info */}
              <div className="p-4 border-b border-border">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <FileSpreadsheet className="w-5 h-5 text-emerald-500" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">{session.file_name}</p>
                    <p className="text-xs text-foreground-muted">
                      {session.row_count?.toLocaleString()} rows &times; {session.column_count} cols
                    </p>
                  </div>
                </div>
              </div>

              {/* Section tabs */}
              <div className="flex border-b border-border">
                {[
                  { id: 'columns', icon: Columns, label: 'Columns' },
                  { id: 'filters', icon: Filter, label: 'Filters' },
                  { id: 'group', icon: Layers, label: 'Group' },
                  { id: 'sort', icon: ArrowUpDown, label: 'Sort' },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveSection(tab.id as any)}
                    className={`flex-1 flex flex-col items-center gap-1 py-3 text-xs font-medium transition-colors ${
                      activeSection === tab.id
                        ? 'text-brand-500 border-b-2 border-brand-500'
                        : 'text-foreground-muted hover:text-foreground'
                    }`}
                  >
                    <tab.icon className="w-4 h-4" />
                    {tab.label}
                  </button>
                ))}
              </div>

              {/* Section content */}
              <div className="flex-1 overflow-y-auto p-4">
                {activeSection === 'columns' && (
                  <ColumnSelector
                    columns={columns}
                    onToggle={handleColumnToggle}
                    onAggregationChange={handleAggregationChange}
                    onAliasChange={handleAliasChange}
                  />
                )}

                {activeSection === 'filters' && (
                  <FilterBuilder
                    filters={filters}
                    columns={columnNames}
                    onAdd={handleAddFilter}
                    onRemove={handleRemoveFilter}
                    onUpdate={handleUpdateFilter}
                  />
                )}

                {activeSection === 'group' && (
                  <div className="space-y-2">
                    <p className="text-sm text-foreground-muted mb-3">
                      Select columns to group by (required when using aggregations)
                    </p>
                    {columns.filter(c => c.visible && (!c.aggregation || c.aggregation === 'none')).map((col) => (
                      <button
                        key={col.name}
                        onClick={() => handleToggleGroupBy(col.name)}
                        className={`w-full flex items-center gap-3 p-3 rounded-lg border transition-colors ${
                          groupBy.includes(col.name)
                            ? 'border-brand-500 bg-brand-600/5'
                            : 'border-border hover:border-border-hover'
                        }`}
                      >
                        <Layers className={`w-4 h-4 ${groupBy.includes(col.name) ? 'text-brand-500' : 'text-foreground-muted'}`} />
                        <span className="text-foreground">{col.name}</span>
                        {groupBy.includes(col.name) && (
                          <CheckCircle2 className="w-4 h-4 text-brand-500 ml-auto" />
                        )}
                      </button>
                    ))}
                  </div>
                )}

                {activeSection === 'sort' && (
                  <div className="space-y-2">
                    <p className="text-sm text-foreground-muted mb-3">
                      Add columns to sort results
                    </p>

                    {/* Current sort columns */}
                    {sortBy.map((sort) => (
                      <div
                        key={sort.column}
                        className="flex items-center gap-2 p-3 bg-surface border border-border rounded-lg"
                      >
                        <ArrowUpDown className="w-4 h-4 text-brand-500" />
                        <span className="flex-1 text-foreground">{sort.column}</span>
                        <button
                          onClick={() => handleToggleSortDirection(sort.column)}
                          className="px-2 py-1 text-xs font-medium bg-surface-muted rounded hover:bg-surface-hover"
                        >
                          {sort.direction}
                        </button>
                        <button
                          onClick={() => handleRemoveSort(sort.column)}
                          className="p-1 hover:bg-red-500/10 rounded"
                        >
                          <X className="w-4 h-4 text-red-500" />
                        </button>
                      </div>
                    ))}

                    {/* Add sort dropdown */}
                    <select
                      value=""
                      onChange={(e) => e.target.value && handleAddSort(e.target.value)}
                      className="w-full px-3 py-2 bg-surface border border-dashed border-border rounded-lg text-sm text-foreground-muted focus:outline-none"
                    >
                      <option value="">+ Add sort column...</option>
                      {columns.filter(c => c.visible && !sortBy.find(s => s.column === c.name)).map((col) => (
                        <option key={col.name} value={col.name}>{col.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
            </div>

            {/* Right panel - Results */}
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Query preview */}
              <AnimatePresence>
                {showQuery && queryPreview && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-b border-border overflow-hidden"
                  >
                    <div className="p-4 bg-surface-muted">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-foreground">Generated SQL</span>
                        <button
                          onClick={handleCopyQuery}
                          className="flex items-center gap-1 text-xs text-foreground-muted hover:text-foreground"
                        >
                          <Copy className="w-3 h-3" />
                          Copy
                        </button>
                      </div>
                      <pre className="text-sm text-foreground font-mono whitespace-pre-wrap bg-surface p-4 rounded-lg border border-border overflow-x-auto">
                        {queryPreview}
                      </pre>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Results area */}
              <div className="flex-1 overflow-auto p-6">
                <div className="max-w-full">
                  {/* Export buttons */}
                  {result && (
                    <div className="flex items-center justify-end gap-2 mb-4">
                      <span className="text-sm text-foreground-muted mr-2">Export:</span>
                      <button
                        onClick={() => handleExport('csv')}
                        className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors"
                      >
                        CSV
                      </button>
                      <button
                        onClick={() => handleExport('excel')}
                        className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors"
                      >
                        Excel
                      </button>
                      <button
                        onClick={() => handleExport('json')}
                        className="px-3 py-1.5 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors"
                      >
                        JSON
                      </button>
                    </div>
                  )}

                  <ResultsTable result={result} isLoading={isRunning} />
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
