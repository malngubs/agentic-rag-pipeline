/**
 * ============================================================================
 * 📄 DOCUMENT PREVIEW - MACROCOMM BI PLATFORM
 * ============================================================================
 */

'use client';

import React, { useState } from 'react';
import {
  FileSpreadsheet,
  FileText,
  ChevronDown,
  ChevronUp,
  Table,
  Check,
  X,
  Database,
} from 'lucide-react';

interface ColumnInfo {
  name: string;
  dtype: string;
  non_null_count?: number;
  null_count?: number;
  unique_count?: number;
  sample_values?: any[];
}

interface DocumentPreviewProps {
  filename: string;
  fileSize: number;
  fileType: string;
  rowCount?: number;
  columnCount?: number;
  columns?: ColumnInfo[];
  vectorChunks?: number;
  isActive?: boolean;
  onClose?: () => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const getFileIcon = (fileType: string) => {
  switch (fileType) {
    case 'excel':
    case 'csv':
      return FileSpreadsheet;
    default:
      return FileText;
  }
};

const formatDtype = (dtype: string): string => {
  if (dtype.includes('int')) return 'Integer';
  if (dtype.includes('float')) return 'Decimal';
  if (dtype.includes('object')) return 'Text';
  if (dtype.includes('datetime')) return 'Date/Time';
  if (dtype.includes('bool')) return 'Boolean';
  return dtype;
};

export const DocumentPreview: React.FC<DocumentPreviewProps> = ({
  filename,
  fileSize,
  fileType,
  rowCount,
  columnCount,
  columns = [],
  vectorChunks = 0,
  isActive = false,
  onClose,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showColumns, setShowColumns] = useState(false);

  const FileIcon = getFileIcon(fileType);
  const isTabular = ['excel', 'csv', 'json', 'parquet'].includes(fileType);

  return (
    <div className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-[var(--color-border)]">
        <div className="w-10 h-10 rounded-lg bg-[var(--color-brand-500)]/10 flex items-center justify-center">
          <FileIcon className="w-5 h-5 text-[var(--color-brand-500)]" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-[var(--color-foreground)] truncate">
              {filename}
            </h4>
            {isActive && (
              <span className="px-2 py-0.5 text-xs font-medium bg-[var(--color-success)]/10 text-[var(--color-success)] rounded-full">
                Active
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 text-sm text-[var(--color-foreground-muted)]">
            <span>{formatFileSize(fileSize)}</span>
            <span>•</span>
            <span className="capitalize">{fileType}</span>
            {vectorChunks > 0 && (
              <>
                <span>•</span>
                <span className="flex items-center gap-1">
                  <Database className="w-3 h-3" />
                  {vectorChunks} chunks indexed
                </span>
              </>
            )}
          </div>
        </div>

        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="p-2 hover:bg-[var(--color-surface-hover)] rounded-lg transition-colors"
        >
          {isExpanded ? (
            <ChevronUp className="w-5 h-5 text-[var(--color-foreground-muted)]" />
          ) : (
            <ChevronDown className="w-5 h-5 text-[var(--color-foreground-muted)]" />
          )}
        </button>

        {onClose && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-[var(--color-surface-hover)] rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-[var(--color-foreground-muted)]" />
          </button>
        )}
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="p-4 space-y-4">
          {isTabular && rowCount !== undefined && columnCount !== undefined && (
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[var(--color-surface-muted)] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[var(--color-foreground)]">
                  {rowCount.toLocaleString()}
                </div>
                <div className="text-xs text-[var(--color-foreground-muted)]">Rows</div>
              </div>
              <div className="bg-[var(--color-surface-muted)] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[var(--color-foreground)]">
                  {columnCount}
                </div>
                <div className="text-xs text-[var(--color-foreground-muted)]">Columns</div>
              </div>
              <div className="bg-[var(--color-surface-muted)] rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-[var(--color-brand-500)]">
                  {vectorChunks}
                </div>
                <div className="text-xs text-[var(--color-foreground-muted)]">Vector Chunks</div>
              </div>
            </div>
          )}

          {isTabular && columns.length > 0 && (
            <div>
              <button
                onClick={() => setShowColumns(!showColumns)}
                className="flex items-center gap-2 text-sm font-medium text-[var(--color-foreground)] hover:text-[var(--color-brand-500)] transition-colors"
              >
                <Table className="w-4 h-4" />
                <span>Column Details ({columns.length})</span>
                {showColumns ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>

              {showColumns && (
                <div className="mt-3 space-y-2 max-h-64 overflow-auto">
                  {columns.slice(0, 20).map((col, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-2 bg-[var(--color-surface-muted)] rounded-lg text-sm"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[var(--color-foreground)]">{col.name}</span>
                        <span className="px-2 py-0.5 text-xs bg-[var(--color-surface)] rounded text-[var(--color-foreground-muted)]">
                          {formatDtype(col.dtype)}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-[var(--color-foreground-muted)]">
                        {col.unique_count !== undefined && <span>{col.unique_count} unique</span>}
                        {col.null_count !== undefined && col.null_count > 0 && (
                          <span className="text-[var(--color-warning)]">{col.null_count} null</span>
                        )}
                      </div>
                    </div>
                  ))}
                  {columns.length > 20 && (
                    <div className="text-center text-sm text-[var(--color-foreground-muted)] py-2">
                      +{columns.length - 20} more columns
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          <div className="border-t border-[var(--color-border)] pt-4">
            <p className="text-sm font-medium text-[var(--color-foreground)] mb-2">You can now:</p>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div className="flex items-center gap-2 text-[var(--color-foreground-muted)]">
                <Check className="w-4 h-4 text-[var(--color-success)]" />
                Ask questions about this data
              </div>
              <div className="flex items-center gap-2 text-[var(--color-foreground-muted)]">
                <Check className="w-4 h-4 text-[var(--color-success)]" />
                Generate visualizations
              </div>
              {isTabular && (
                <>
                  <div className="flex items-center gap-2 text-[var(--color-foreground-muted)]">
                    <Check className="w-4 h-4 text-[var(--color-success)]" />
                    Run statistical analysis
                  </div>
                  <div className="flex items-center gap-2 text-[var(--color-foreground-muted)]">
                    <Check className="w-4 h-4 text-[var(--color-success)]" />
                    Create forecasts
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentPreview;
