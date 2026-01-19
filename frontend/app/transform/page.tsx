/**
 * ============================================================================
 * DATA TRANSFORMATION UI - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Visual data transformation and cleaning:
 * - Clean and validate data
 * - Transform columns (rename, type cast, split, merge)
 * - Filter and sort operations
 * - Merge multiple datasets
 * - Export transformed data
 */

'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { api, AnalysisSession, DataProfile } from '@/lib/api/client';
import {
  Wand2,
  Upload,
  FileSpreadsheet,
  Loader2,
  AlertCircle,
  X,
  Plus,
  Trash2,
  ChevronRight,
  ChevronDown,
  Check,
  Play,
  Download,
  RotateCcw,
  Eye,
  EyeOff,
  ArrowRight,
  Merge,
  Split,
  Filter,
  ArrowUpDown,
  Type,
  Hash,
  Calendar,
  ToggleLeft,
  Replace,
  Scissors,
  SortAsc,
  Copy,
  Eraser,
  Table,
  Layers,
  GitMerge,
  RefreshCw,
  Settings,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

type TransformationType =
  | 'rename'
  | 'change_type'
  | 'fill_missing'
  | 'remove_duplicates'
  | 'filter'
  | 'sort'
  | 'split_column'
  | 'merge_columns'
  | 'extract'
  | 'replace'
  | 'trim'
  | 'uppercase'
  | 'lowercase'
  | 'round'
  | 'calculate';

interface TransformationStep {
  id: string;
  type: TransformationType;
  config: Record<string, any>;
  column?: string;
  description: string;
  isEnabled: boolean;
  preview?: {
    before: any;
    after: any;
  };
}

interface ColumnInfo {
  name: string;
  type: string;
  nullCount: number;
  uniqueCount: number;
  sampleValues: any[];
  issues: string[];
}

interface DataQualityIssue {
  column: string;
  type: 'missing' | 'duplicate' | 'outlier' | 'invalid' | 'inconsistent';
  severity: 'low' | 'medium' | 'high';
  count: number;
  description: string;
  suggestion: string;
}

// =============================================================================
// CONSTANTS
// =============================================================================

const TRANSFORMATION_TYPES: {
  id: TransformationType;
  label: string;
  description: string;
  icon: typeof Wand2;
  category: 'clean' | 'transform' | 'structure';
}[] = [
  { id: 'fill_missing', label: 'Fill Missing', description: 'Replace null/empty values', icon: Eraser, category: 'clean' },
  { id: 'remove_duplicates', label: 'Remove Duplicates', description: 'Remove duplicate rows', icon: Copy, category: 'clean' },
  { id: 'trim', label: 'Trim Whitespace', description: 'Remove leading/trailing spaces', icon: Scissors, category: 'clean' },
  { id: 'replace', label: 'Find & Replace', description: 'Replace specific values', icon: Replace, category: 'clean' },
  { id: 'rename', label: 'Rename Column', description: 'Change column name', icon: Type, category: 'structure' },
  { id: 'change_type', label: 'Change Type', description: 'Convert data type', icon: Hash, category: 'structure' },
  { id: 'split_column', label: 'Split Column', description: 'Split into multiple columns', icon: Split, category: 'structure' },
  { id: 'merge_columns', label: 'Merge Columns', description: 'Combine multiple columns', icon: Merge, category: 'structure' },
  { id: 'filter', label: 'Filter Rows', description: 'Remove rows by condition', icon: Filter, category: 'transform' },
  { id: 'sort', label: 'Sort', description: 'Order rows by column', icon: SortAsc, category: 'transform' },
  { id: 'uppercase', label: 'Uppercase', description: 'Convert text to uppercase', icon: Type, category: 'transform' },
  { id: 'lowercase', label: 'Lowercase', description: 'Convert text to lowercase', icon: Type, category: 'transform' },
  { id: 'round', label: 'Round Numbers', description: 'Round to decimal places', icon: Hash, category: 'transform' },
  { id: 'extract', label: 'Extract', description: 'Extract part of text', icon: Scissors, category: 'transform' },
  { id: 'calculate', label: 'Calculate', description: 'Create calculated column', icon: Wand2, category: 'transform' },
];

const DATA_TYPES = [
  { value: 'string', label: 'Text' },
  { value: 'integer', label: 'Integer' },
  { value: 'float', label: 'Decimal' },
  { value: 'date', label: 'Date' },
  { value: 'datetime', label: 'Date & Time' },
  { value: 'boolean', label: 'Boolean' },
];

const FILL_STRATEGIES = [
  { value: 'constant', label: 'Constant value' },
  { value: 'mean', label: 'Mean (numeric)' },
  { value: 'median', label: 'Median (numeric)' },
  { value: 'mode', label: 'Most common value' },
  { value: 'forward', label: 'Forward fill' },
  { value: 'backward', label: 'Backward fill' },
];

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const ColumnCard: React.FC<{
  column: ColumnInfo;
  onTransform: (type: TransformationType) => void;
}> = ({ column, onTransform }) => {
  const [expanded, setExpanded] = useState(false);
  const hasIssues = column.issues.length > 0;

  const getTypeIcon = () => {
    if (column.type.includes('int') || column.type.includes('float')) return Hash;
    if (column.type.includes('date') || column.type.includes('time')) return Calendar;
    if (column.type.includes('bool')) return ToggleLeft;
    return Type;
  };

  const TypeIcon = getTypeIcon();

  return (
    <div className={`bg-surface border rounded-xl transition-colors ${
      hasIssues ? 'border-amber-500/50' : 'border-border'
    }`}>
      <div
        className="flex items-center gap-3 p-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="w-8 h-8 rounded-lg bg-brand-600/10 flex items-center justify-center">
          <TypeIcon className="w-4 h-4 text-brand-500" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-foreground truncate">{column.name}</p>
          <p className="text-xs text-foreground-muted">{column.type}</p>
        </div>
        {hasIssues && (
          <div className="flex items-center gap-1 px-2 py-0.5 bg-amber-500/10 rounded">
            <AlertTriangle className="w-3 h-3 text-amber-500" />
            <span className="text-xs text-amber-500">{column.issues.length}</span>
          </div>
        )}
        {expanded ? (
          <ChevronDown className="w-4 h-4 text-foreground-muted" />
        ) : (
          <ChevronRight className="w-4 h-4 text-foreground-muted" />
        )}
      </div>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-border"
          >
            <div className="p-3 space-y-3">
              {/* Stats */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="p-2 bg-surface-muted rounded">
                  <span className="text-foreground-muted">Unique</span>
                  <p className="font-medium text-foreground">{column.uniqueCount}</p>
                </div>
                <div className="p-2 bg-surface-muted rounded">
                  <span className="text-foreground-muted">Missing</span>
                  <p className={`font-medium ${column.nullCount > 0 ? 'text-amber-500' : 'text-foreground'}`}>
                    {column.nullCount}
                  </p>
                </div>
              </div>

              {/* Sample values */}
              <div>
                <p className="text-xs text-foreground-muted mb-1">Sample values</p>
                <div className="flex flex-wrap gap-1">
                  {column.sampleValues.slice(0, 5).map((val, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 text-xs bg-surface-muted text-foreground rounded"
                    >
                      {val === null ? 'null' : String(val)}
                    </span>
                  ))}
                </div>
              </div>

              {/* Issues */}
              {hasIssues && (
                <div className="p-2 bg-amber-500/10 rounded-lg">
                  <p className="text-xs font-medium text-amber-500 mb-1">Issues detected</p>
                  {column.issues.map((issue, idx) => (
                    <p key={idx} className="text-xs text-amber-600">{issue}</p>
                  ))}
                </div>
              )}

              {/* Quick actions */}
              <div className="flex flex-wrap gap-1">
                <button
                  onClick={() => onTransform('rename')}
                  className="px-2 py-1 text-xs bg-surface-muted hover:bg-surface-hover rounded transition-colors"
                >
                  Rename
                </button>
                <button
                  onClick={() => onTransform('change_type')}
                  className="px-2 py-1 text-xs bg-surface-muted hover:bg-surface-hover rounded transition-colors"
                >
                  Change Type
                </button>
                {column.nullCount > 0 && (
                  <button
                    onClick={() => onTransform('fill_missing')}
                    className="px-2 py-1 text-xs bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 rounded transition-colors"
                  >
                    Fill Missing
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

const TransformationStepCard: React.FC<{
  step: TransformationStep;
  index: number;
  onToggle: () => void;
  onRemove: () => void;
  onEdit: () => void;
}> = ({ step, index, onToggle, onRemove, onEdit }) => {
  const transform = TRANSFORMATION_TYPES.find(t => t.id === step.type);
  const Icon = transform?.icon || Wand2;

  return (
    <div className={`bg-surface border rounded-xl p-3 transition-all ${
      step.isEnabled ? 'border-border' : 'border-border/50 opacity-50'
    }`}>
      <div className="flex items-center gap-3">
        <div className="w-6 h-6 rounded-full bg-brand-600/10 flex items-center justify-center text-xs font-medium text-brand-500">
          {index + 1}
        </div>
        <div className="w-8 h-8 rounded-lg bg-surface-muted flex items-center justify-center">
          <Icon className="w-4 h-4 text-foreground-muted" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-medium text-sm text-foreground">{transform?.label}</p>
          <p className="text-xs text-foreground-muted truncate">{step.description}</p>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={onToggle}
            className={`p-1.5 rounded transition-colors ${
              step.isEnabled
                ? 'bg-emerald-500/10 text-emerald-500'
                : 'bg-surface-muted text-foreground-muted'
            }`}
          >
            {step.isEnabled ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
          </button>
          <button onClick={onEdit} className="p-1.5 hover:bg-surface-hover rounded">
            <Settings className="w-4 h-4 text-foreground-muted" />
          </button>
          <button onClick={onRemove} className="p-1.5 hover:bg-red-500/10 rounded">
            <Trash2 className="w-4 h-4 text-red-500" />
          </button>
        </div>
      </div>
    </div>
  );
};

const DataQualityCard: React.FC<{
  issue: DataQualityIssue;
  onFix: () => void;
}> = ({ issue, onFix }) => {
  const severityColors = {
    low: 'border-blue-500/50 bg-blue-500/5',
    medium: 'border-amber-500/50 bg-amber-500/5',
    high: 'border-red-500/50 bg-red-500/5',
  };

  const severityTextColors = {
    low: 'text-blue-500',
    medium: 'text-amber-500',
    high: 'text-red-500',
  };

  return (
    <div className={`border rounded-xl p-4 ${severityColors[issue.severity]}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className={`w-4 h-4 ${severityTextColors[issue.severity]}`} />
          <span className="font-medium text-foreground">{issue.column}</span>
        </div>
        <span className={`px-2 py-0.5 text-xs font-medium rounded capitalize ${severityTextColors[issue.severity]} bg-white/50`}>
          {issue.severity}
        </span>
      </div>
      <p className="text-sm text-foreground-secondary mb-2">{issue.description}</p>
      <p className="text-xs text-foreground-muted mb-3">{issue.count} occurrences</p>
      <div className="flex items-center justify-between">
        <p className="text-xs text-brand-500">{issue.suggestion}</p>
        <button
          onClick={onFix}
          className="px-3 py-1 text-xs font-medium bg-brand-600 hover:bg-brand-500 text-white rounded transition-colors"
        >
          Auto-fix
        </button>
      </div>
    </div>
  );
};

// =============================================================================
// MODAL COMPONENTS
// =============================================================================

interface AddTransformModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (step: TransformationStep) => void;
  columns: string[];
  selectedColumn?: string;
  selectedType?: TransformationType;
}

const AddTransformModal: React.FC<AddTransformModalProps> = ({
  isOpen,
  onClose,
  onAdd,
  columns,
  selectedColumn,
  selectedType,
}) => {
  const [type, setType] = useState<TransformationType>(selectedType || 'rename');
  const [column, setColumn] = useState(selectedColumn || columns[0] || '');
  const [config, setConfig] = useState<Record<string, any>>({});

  useEffect(() => {
    if (selectedType) setType(selectedType);
    if (selectedColumn) setColumn(selectedColumn);
  }, [selectedType, selectedColumn]);

  const handleAdd = () => {
    const transform = TRANSFORMATION_TYPES.find(t => t.id === type);
    const step: TransformationStep = {
      id: `step-${Date.now()}`,
      type,
      column,
      config,
      description: generateDescription(type, column, config),
      isEnabled: true,
    };
    onAdd(step);
    onClose();
    setConfig({});
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface border border-border rounded-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
      >
        <div className="p-6 border-b border-border">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-foreground">Add Transformation</h2>
            <button onClick={onClose} className="p-1 hover:bg-surface-hover rounded">
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {/* Transformation type */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">Transformation Type</label>
            <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
              {TRANSFORMATION_TYPES.map((t) => (
                <button
                  key={t.id}
                  onClick={() => setType(t.id)}
                  className={`flex items-center gap-2 p-2 rounded-lg text-left transition-colors ${
                    type === t.id
                      ? 'bg-brand-600/10 border border-brand-500'
                      : 'bg-surface-muted hover:bg-surface-hover border border-transparent'
                  }`}
                >
                  <t.icon className={`w-4 h-4 ${type === t.id ? 'text-brand-500' : 'text-foreground-muted'}`} />
                  <div>
                    <p className="text-sm font-medium text-foreground">{t.label}</p>
                    <p className="text-xs text-foreground-muted">{t.description}</p>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Column selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-1">Column</label>
            <select
              value={column}
              onChange={(e) => setColumn(e.target.value)}
              className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
            >
              {columns.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>

          {/* Type-specific configuration */}
          {type === 'rename' && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">New Name</label>
              <input
                type="text"
                value={config.newName || ''}
                onChange={(e) => setConfig({ ...config, newName: e.target.value })}
                placeholder="Enter new column name"
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              />
            </div>
          )}

          {type === 'change_type' && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">New Type</label>
              <select
                value={config.newType || 'string'}
                onChange={(e) => setConfig({ ...config, newType: e.target.value })}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              >
                {DATA_TYPES.map((dt) => (
                  <option key={dt.value} value={dt.value}>{dt.label}</option>
                ))}
              </select>
            </div>
          )}

          {type === 'fill_missing' && (
            <>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Strategy</label>
                <select
                  value={config.strategy || 'constant'}
                  onChange={(e) => setConfig({ ...config, strategy: e.target.value })}
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                >
                  {FILL_STRATEGIES.map((s) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>
              {config.strategy === 'constant' && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Fill Value</label>
                  <input
                    type="text"
                    value={config.fillValue || ''}
                    onChange={(e) => setConfig({ ...config, fillValue: e.target.value })}
                    placeholder="Enter value"
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                  />
                </div>
              )}
            </>
          )}

          {type === 'filter' && (
            <>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Operator</label>
                <select
                  value={config.operator || 'equals'}
                  onChange={(e) => setConfig({ ...config, operator: e.target.value })}
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                >
                  <option value="equals">Equals</option>
                  <option value="not_equals">Not equals</option>
                  <option value="greater_than">Greater than</option>
                  <option value="less_than">Less than</option>
                  <option value="contains">Contains</option>
                  <option value="is_null">Is null</option>
                  <option value="is_not_null">Is not null</option>
                </select>
              </div>
              {!['is_null', 'is_not_null'].includes(config.operator) && (
                <div>
                  <label className="block text-sm font-medium text-foreground mb-1">Value</label>
                  <input
                    type="text"
                    value={config.value || ''}
                    onChange={(e) => setConfig({ ...config, value: e.target.value })}
                    placeholder="Enter value"
                    className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                  />
                </div>
              )}
            </>
          )}

          {type === 'replace' && (
            <>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Find</label>
                <input
                  type="text"
                  value={config.find || ''}
                  onChange={(e) => setConfig({ ...config, find: e.target.value })}
                  placeholder="Text to find"
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Replace with</label>
                <input
                  type="text"
                  value={config.replace || ''}
                  onChange={(e) => setConfig({ ...config, replace: e.target.value })}
                  placeholder="Replacement text"
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                />
              </div>
            </>
          )}

          {type === 'round' && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Decimal Places</label>
              <input
                type="number"
                min={0}
                max={10}
                value={config.decimals || 2}
                onChange={(e) => setConfig({ ...config, decimals: parseInt(e.target.value) })}
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              />
            </div>
          )}

          {type === 'split_column' && (
            <div>
              <label className="block text-sm font-medium text-foreground mb-1">Delimiter</label>
              <input
                type="text"
                value={config.delimiter || ','}
                onChange={(e) => setConfig({ ...config, delimiter: e.target.value })}
                placeholder="e.g., comma, space, etc."
                className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
              />
            </div>
          )}

          {type === 'merge_columns' && (
            <>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Second Column</label>
                <select
                  value={config.column2 || columns[1] || ''}
                  onChange={(e) => setConfig({ ...config, column2: e.target.value })}
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                >
                  {columns.filter(c => c !== column).map((col) => (
                    <option key={col} value={col}>{col}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-foreground mb-1">Separator</label>
                <input
                  type="text"
                  value={config.separator || ' '}
                  onChange={(e) => setConfig({ ...config, separator: e.target.value })}
                  placeholder="e.g., space, dash, etc."
                  className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                />
              </div>
            </>
          )}
        </div>

        <div className="p-6 border-t border-border flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleAdd}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors"
          >
            Add Transformation
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

function generateDescription(type: TransformationType, column: string, config: Record<string, any>): string {
  switch (type) {
    case 'rename':
      return `Rename "${column}" to "${config.newName || 'new_name'}"`;
    case 'change_type':
      return `Change "${column}" type to ${config.newType || 'string'}`;
    case 'fill_missing':
      return `Fill missing values in "${column}" using ${config.strategy || 'constant'}`;
    case 'remove_duplicates':
      return `Remove duplicate rows based on "${column}"`;
    case 'filter':
      return `Filter rows where "${column}" ${config.operator || 'equals'} ${config.value || ''}`;
    case 'sort':
      return `Sort by "${column}" ${config.direction || 'ascending'}`;
    case 'trim':
      return `Trim whitespace in "${column}"`;
    case 'uppercase':
      return `Convert "${column}" to uppercase`;
    case 'lowercase':
      return `Convert "${column}" to lowercase`;
    case 'replace':
      return `Replace "${config.find || ''}" with "${config.replace || ''}" in "${column}"`;
    case 'round':
      return `Round "${column}" to ${config.decimals || 2} decimal places`;
    case 'split_column':
      return `Split "${column}" by "${config.delimiter || ','}"`;
    case 'merge_columns':
      return `Merge "${column}" with "${config.column2 || ''}"`;
    case 'extract':
      return `Extract pattern from "${column}"`;
    case 'calculate':
      return `Create calculated column from "${column}"`;
    default:
      return `Transform "${column}"`;
  }
}

// =============================================================================
// MAIN TRANSFORM PAGE
// =============================================================================

export default function TransformPage() {
  // Session state
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [profile, setProfile] = useState<DataProfile | null>(null);

  // Column info
  const [columns, setColumns] = useState<ColumnInfo[]>([]);
  const [qualityIssues, setQualityIssues] = useState<DataQualityIssue[]>([]);

  // Transformation pipeline
  const [steps, setSteps] = useState<TransformationStep[]>([]);

  // UI state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isApplying, setIsApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedColumn, setSelectedColumn] = useState<string | undefined>();
  const [selectedType, setSelectedType] = useState<TransformationType | undefined>();
  const [activePanel, setActivePanel] = useState<'columns' | 'quality' | 'preview'>('columns');

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

      // Convert profile to column info
      const columnInfos: ColumnInfo[] = profileData.columns.map((col) => ({
        name: col.name,
        type: col.type,
        nullCount: col.missing_count,
        uniqueCount: col.unique_count,
        sampleValues: col.sample_values,
        issues: generateColumnIssues(col),
      }));
      setColumns(columnInfos);

      // Generate quality issues
      const issues = generateQualityIssues(profileData);
      setQualityIssues(issues);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [session]);

  // Handle add transformation
  const handleAddStep = useCallback((step: TransformationStep) => {
    setSteps(prev => [...prev, step]);
  }, []);

  // Handle remove step
  const handleRemoveStep = useCallback((id: string) => {
    setSteps(prev => prev.filter(s => s.id !== id));
  }, []);

  // Handle toggle step
  const handleToggleStep = useCallback((id: string) => {
    setSteps(prev => prev.map(s =>
      s.id === id ? { ...s, isEnabled: !s.isEnabled } : s
    ));
  }, []);

  // Handle transform column
  const handleTransformColumn = useCallback((column: string, type: TransformationType) => {
    setSelectedColumn(column);
    setSelectedType(type);
    setShowAddModal(true);
  }, []);

  // Handle fix quality issue
  const handleFixIssue = useCallback((issue: DataQualityIssue) => {
    const step: TransformationStep = {
      id: `step-${Date.now()}`,
      type: issue.type === 'missing' ? 'fill_missing' : 'remove_duplicates',
      column: issue.column,
      config: issue.type === 'missing' ? { strategy: 'mean' } : {},
      description: issue.suggestion,
      isEnabled: true,
    };
    setSteps(prev => [...prev, step]);
    setQualityIssues(prev => prev.filter(i => i !== issue));
  }, []);

  // Apply transformations
  const handleApplyTransformations = useCallback(async () => {
    if (!session?.id) return;

    setIsApplying(true);
    setError(null);

    try {
      // In a real implementation, this would send the transformation pipeline to the backend
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Clear steps after applying
      // setSteps([]);

      // Show success
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to apply transformations');
    } finally {
      setIsApplying(false);
    }
  }, [session?.id]);

  // Export transformed data
  const handleExport = useCallback(async (format: 'csv' | 'excel' | 'json') => {
    if (!session?.id) return;

    try {
      const blob = await api.session.export(session.id, format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `transformed_data.${format === 'excel' ? 'xlsx' : format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Export failed');
    }
  }, [session?.id]);

  const enabledStepsCount = steps.filter(s => s.isEnabled).length;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-hidden bg-background flex flex-col">
        {/* Header */}
        <div className="border-b border-border p-6">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">Data Transformation</h1>
              <p className="text-foreground-secondary">
                Clean, transform, and prepare your data visually
              </p>
            </div>
            {session?.data_loaded && (
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setSteps([])}
                  disabled={steps.length === 0}
                  className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors disabled:opacity-50"
                >
                  <RotateCcw className="w-4 h-4" />
                  Reset
                </button>
                <button
                  onClick={handleApplyTransformations}
                  disabled={isApplying || enabledStepsCount === 0}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {isApplying ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Apply ({enabledStepsCount})
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
                <Wand2 className="w-10 h-10 text-brand-500" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Data Transformation</h2>
              <p className="text-foreground-muted mb-8">
                Upload your data to clean, transform, and prepare it for analysis
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
                    Processing... {uploadProgress}%
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload Data File
                  </>
                )}
              </button>

              <div className="mt-8 grid grid-cols-3 gap-4 text-left">
                <div className="p-3 bg-surface rounded-lg border border-border">
                  <Eraser className="w-5 h-5 text-brand-500 mb-2" />
                  <p className="text-sm font-medium text-foreground">Clean</p>
                  <p className="text-xs text-foreground-muted">Remove nulls & duplicates</p>
                </div>
                <div className="p-3 bg-surface rounded-lg border border-border">
                  <Wand2 className="w-5 h-5 text-brand-500 mb-2" />
                  <p className="text-sm font-medium text-foreground">Transform</p>
                  <p className="text-xs text-foreground-muted">Modify & calculate</p>
                </div>
                <div className="p-3 bg-surface rounded-lg border border-border">
                  <GitMerge className="w-5 h-5 text-brand-500 mb-2" />
                  <p className="text-sm font-medium text-foreground">Merge</p>
                  <p className="text-xs text-foreground-muted">Combine datasets</p>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* Transformation interface */
          <div className="flex-1 overflow-hidden flex">
            {/* Left panel - Columns & Quality */}
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
                      {session.row_count?.toLocaleString()} rows
                    </p>
                  </div>
                </div>
              </div>

              {/* Panel tabs */}
              <div className="flex border-b border-border">
                {[
                  { id: 'columns', label: 'Columns', count: columns.length },
                  { id: 'quality', label: 'Quality', count: qualityIssues.length },
                ].map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActivePanel(tab.id as any)}
                    className={`flex-1 py-3 text-sm font-medium transition-colors ${
                      activePanel === tab.id
                        ? 'text-brand-500 border-b-2 border-brand-500'
                        : 'text-foreground-muted hover:text-foreground'
                    }`}
                  >
                    {tab.label}
                    {tab.count > 0 && (
                      <span className={`ml-1 px-1.5 py-0.5 text-xs rounded ${
                        tab.id === 'quality' && tab.count > 0
                          ? 'bg-amber-500/10 text-amber-500'
                          : 'bg-surface-muted text-foreground-muted'
                      }`}>
                        {tab.count}
                      </span>
                    )}
                  </button>
                ))}
              </div>

              {/* Panel content */}
              <div className="flex-1 overflow-y-auto p-4 space-y-2">
                {activePanel === 'columns' && columns.map((column) => (
                  <ColumnCard
                    key={column.name}
                    column={column}
                    onTransform={(type) => handleTransformColumn(column.name, type)}
                  />
                ))}

                {activePanel === 'quality' && (
                  qualityIssues.length === 0 ? (
                    <div className="text-center py-8">
                      <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-4" />
                      <p className="font-medium text-foreground">Data looks good!</p>
                      <p className="text-sm text-foreground-muted">No quality issues detected</p>
                    </div>
                  ) : (
                    qualityIssues.map((issue, idx) => (
                      <DataQualityCard
                        key={idx}
                        issue={issue}
                        onFix={() => handleFixIssue(issue)}
                      />
                    ))
                  )
                )}
              </div>
            </div>

            {/* Middle panel - Transformation pipeline */}
            <div className="w-96 border-r border-border flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-foreground">Transformation Pipeline</h3>
                  <button
                    onClick={() => {
                      setSelectedColumn(undefined);
                      setSelectedType(undefined);
                      setShowAddModal(true);
                    }}
                    className="flex items-center gap-1 px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-sm rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    Add Step
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4">
                {steps.length === 0 ? (
                  <div className="text-center py-12">
                    <Layers className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                    <p className="text-foreground-muted">No transformations added</p>
                    <p className="text-sm text-foreground-muted mt-1">
                      Click on a column or use &quot;Add Step&quot; to begin
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {steps.map((step, index) => (
                      <TransformationStepCard
                        key={step.id}
                        step={step}
                        index={index}
                        onToggle={() => handleToggleStep(step.id)}
                        onRemove={() => handleRemoveStep(step.id)}
                        onEdit={() => {}}
                      />
                    ))}
                  </div>
                )}
              </div>

              {/* Export options */}
              {steps.length > 0 && (
                <div className="p-4 border-t border-border">
                  <p className="text-sm font-medium text-foreground mb-3">Export Transformed Data</p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleExport('csv')}
                      className="flex-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors"
                    >
                      CSV
                    </button>
                    <button
                      onClick={() => handleExport('excel')}
                      className="flex-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors"
                    >
                      Excel
                    </button>
                    <button
                      onClick={() => handleExport('json')}
                      className="flex-1 px-3 py-2 text-sm border border-border rounded-lg hover:bg-surface-hover transition-colors"
                    >
                      JSON
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Right panel - Preview */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-foreground">Data Preview</h3>
                  <button className="flex items-center gap-1 text-sm text-foreground-muted hover:text-foreground">
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                  </button>
                </div>
              </div>

              <div className="flex-1 overflow-auto p-4">
                {profile && (
                  <div className="overflow-x-auto border border-border rounded-lg">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="bg-surface-muted border-b border-border">
                          {profile.columns.slice(0, 8).map((col) => (
                            <th
                              key={col.name}
                              className="px-3 py-2 text-left font-medium text-foreground whitespace-nowrap"
                            >
                              {col.name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {Array.from({ length: 10 }).map((_, rowIdx) => (
                          <tr key={rowIdx} className="border-b border-border/50">
                            {profile.columns.slice(0, 8).map((col) => (
                              <td
                                key={col.name}
                                className="px-3 py-2 text-foreground whitespace-nowrap"
                              >
                                {col.sample_values[rowIdx] !== undefined
                                  ? String(col.sample_values[rowIdx])
                                  : '-'}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Add transformation modal */}
      <AddTransformModal
        isOpen={showAddModal}
        onClose={() => {
          setShowAddModal(false);
          setSelectedColumn(undefined);
          setSelectedType(undefined);
        }}
        onAdd={handleAddStep}
        columns={columns.map(c => c.name)}
        selectedColumn={selectedColumn}
        selectedType={selectedType}
      />
    </div>
  );
}

// =============================================================================
// DATA QUALITY HELPERS
// =============================================================================

function generateColumnIssues(col: DataProfile['columns'][0]): string[] {
  const issues: string[] = [];

  if (col.missing_percentage > 10) {
    issues.push(`${col.missing_percentage.toFixed(1)}% missing values`);
  }

  if (col.unique_count === 1) {
    issues.push('Only one unique value (constant)');
  }

  return issues;
}

function generateQualityIssues(profile: DataProfile): DataQualityIssue[] {
  const issues: DataQualityIssue[] = [];

  profile.columns.forEach((col) => {
    if (col.missing_count > 0) {
      issues.push({
        column: col.name,
        type: 'missing',
        severity: col.missing_percentage > 20 ? 'high' : col.missing_percentage > 5 ? 'medium' : 'low',
        count: col.missing_count,
        description: `${col.missing_count} missing values (${col.missing_percentage.toFixed(1)}%)`,
        suggestion: `Fill missing values in "${col.name}" with mean/median`,
      });
    }
  });

  return issues;
}
