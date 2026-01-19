/**
 * ============================================================================
 * 📋 DATA TABLE - Interactive Data Display
 * ============================================================================
 */

'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Download } from 'lucide-react';

interface DataTableProps {
  data: Array<Record<string, any>>;
  title?: string;
  maxRows?: number;
}

export const DataTable: React.FC<DataTableProps> = ({
  data,
  title,
  maxRows = 10,
}) => {
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [currentPage, setCurrentPage] = useState(1);

  if (!data || data.length === 0) {
    return (
      <div className="glass border border-white/10 p-8 rounded-xl text-center">
        <p className="text-foreground-muted">No data available</p>
      </div>
    );
  }

  const columns = Object.keys(data[0]);

  // Sorting
  const sortedData = [...data].sort((a, b) => {
    if (!sortColumn) return 0;
    const aVal = a[sortColumn];
    const bVal = b[sortColumn];

    if (typeof aVal === 'number' && typeof bVal === 'number') {
      return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
    }

    const aStr = String(aVal).toLowerCase();
    const bStr = String(bVal).toLowerCase();
    if (sortDirection === 'asc') {
      return aStr < bStr ? -1 : aStr > bStr ? 1 : 0;
    } else {
      return aStr > bStr ? -1 : aStr < bStr ? 1 : 0;
    }
  });

  // Pagination
  const totalPages = Math.ceil(data.length / maxRows);
  const startIndex = (currentPage - 1) * maxRows;
  const paginatedData = sortedData.slice(startIndex, startIndex + maxRows);

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const formatValue = (value: any) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      return value.toLocaleString('en-US', { maximumFractionDigits: 2 });
    }
    return String(value);
  };

  return (
    <div className="glass border border-white/10 rounded-xl overflow-hidden">
      {/* Header */}
      {title && (
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-foreground">{title}</h3>
          <button className="p-2 hover:bg-surface-hover rounded-lg transition-colors">
            <Download className="w-4 h-4 text-foreground-muted" />
          </button>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-surface-muted">
            <tr>
              {columns.map((column) => (
                <th
                  key={column}
                  onClick={() => handleSort(column)}
                  className="px-4 py-3 text-left text-sm font-medium text-foreground-muted cursor-pointer hover:bg-surface-hover transition-colors"
                >
                  <div className="flex items-center gap-2">
                    {column}
                    {sortColumn === column && (
                      sortDirection === 'asc' ? (
                        <ChevronUp className="w-3 h-3" />
                      ) : (
                        <ChevronDown className="w-3 h-3" />
                      )
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className="border-t border-border hover:bg-surface-hover transition-colors"
              >
                {columns.map((column) => (
                  <td
                    key={column}
                    className="px-4 py-3 text-sm text-foreground"
                  >
                    {formatValue(row[column])}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-4 border-t border-border flex items-center justify-between">
          <p className="text-sm text-foreground-muted">
            Showing {startIndex + 1}-{Math.min(startIndex + maxRows, data.length)} of {data.length} rows
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded-lg border border-border hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              Previous
            </button>
            <span className="text-sm text-foreground-muted">
              Page {currentPage} of {totalPages}
            </span>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded-lg border border-border hover:bg-surface-hover disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
