/**
 * ============================================================================
 * 📊 DATASET SELECTOR - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Unified dataset selector component.
 * Shows active dataset and allows switching between uploaded datasets.
 *
 * Features:
 * - Display active dataset info
 * - Dropdown to switch datasets
 * - Quick upload button
 * - Dataset statistics
 */
 
'use client';
 
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Database,
  ChevronDown,
  Upload,
  Check,
  FileSpreadsheet,
  FileText,
  Table,
  X,
  Loader2,
  AlertCircle,
  Trash2,
} from 'lucide-react';
import { api, DatasetMetadata } from '@/lib/api/client';
 
// =============================================================================
// TYPES
// =============================================================================
 
interface DatasetSelectorProps {
  className?: string;
  compact?: boolean;
  onDatasetChange?: (dataset: DatasetMetadata | null) => void;
}
 
// =============================================================================
// FILE TYPE ICONS
// =============================================================================
 
const getFileIcon = (fileType: string) => {
  switch (fileType) {
    case 'excel':
      return FileSpreadsheet;
    case 'csv':
      return Table;
    default:
      return FileText;
  }
};
 
// =============================================================================
// COMPONENT
// =============================================================================
 
export const DatasetSelector: React.FC<DatasetSelectorProps> = ({
  className = '',
  compact = false,
  onDatasetChange,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [activeDataset, setActiveDataset] = useState<DatasetMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
 
  // Load datasets on mount
  const loadDatasets = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await api.dataset.list();
      setDatasets(response.datasets);
 
      // Find active dataset
      const active = response.datasets.find(d => d.is_active);
      setActiveDataset(active || null);
 
      if (onDatasetChange && active) {
        onDatasetChange(active);
      }
    } catch (err) {
      console.error('Failed to load datasets:', err);
      setError('Failed to load datasets');
    } finally {
      setIsLoading(false);
    }
  }, [onDatasetChange]);
 
  useEffect(() => {
    loadDatasets();
  }, [loadDatasets]);
 
  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
 
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
 
  // Handle dataset selection
  const handleSelectDataset = async (dataset: DatasetMetadata) => {
    try {
      await api.dataset.setActive(dataset.id);
      setActiveDataset(dataset);
      setIsOpen(false);
 
      if (onDatasetChange) {
        onDatasetChange(dataset);
      }
    } catch (err) {
      console.error('Failed to set active dataset:', err);
      setError('Failed to switch dataset');
    }
  };
 
  // Handle file upload
  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
 
    try {
      setIsUploading(true);
      setUploadProgress(0);
      setError(null);
 
      const result = await api.dataset.upload(file, (progress) => {
        setUploadProgress(progress);
      });
 
      if (result.success) {
        await loadDatasets();
      } else {
        setError(result.message);
      }
    } catch (err) {
      console.error('Upload failed:', err);
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };
 
  // Handle delete
  const handleDelete = async (e: React.MouseEvent, datasetId: string) => {
    e.stopPropagation();
 
    if (!confirm('Are you sure you want to delete this dataset?')) return;
 
    try {
      await api.dataset.delete(datasetId);
      await loadDatasets();
    } catch (err) {
      console.error('Failed to delete dataset:', err);
      setError('Failed to delete dataset');
    }
  };
 
  const FileIcon = activeDataset ? getFileIcon(activeDataset.file_type) : Database;
 
  // Compact view (for sidebar)
  if (compact) {
    return (
      <div className={`relative ${className}`} ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-surface border border-border hover:bg-surface-hover transition-colors"
        >
          <FileIcon className="w-4 h-4 text-brand-500" />
          <span className="flex-1 text-sm text-foreground truncate text-left">
            {isLoading ? 'Loading...' : activeDataset?.original_filename || 'No dataset'}
          </span>
          <ChevronDown className={`w-4 h-4 text-foreground-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>
 
        <AnimatePresence>
          {isOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="absolute top-full left-0 right-0 mt-1 bg-surface border border-border rounded-lg shadow-lg z-50 max-h-64 overflow-auto"
            >
              {/* Upload button */}
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="w-full flex items-center gap-2 px-3 py-2 text-sm text-brand-500 hover:bg-surface-hover border-b border-border"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Uploading... {uploadProgress}%</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    <span>Upload New Dataset</span>
                  </>
                )}
              </button>
 
              {/* Dataset list */}
              {datasets.length === 0 ? (
                <div className="px-3 py-4 text-sm text-foreground-muted text-center">
                  No datasets uploaded yet
                </div>
              ) : (
                datasets.map((dataset) => {
                  const Icon = getFileIcon(dataset.file_type);
                  return (
                    <button
                      key={dataset.id}
                      onClick={() => handleSelectDataset(dataset)}
                      className={`w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-surface-hover ${
                        dataset.is_active ? 'bg-brand-500/10' : ''
                      }`}
                    >
                      <Icon className="w-4 h-4 text-foreground-muted" />
                      <span className="flex-1 truncate text-left">{dataset.original_filename}</span>
                      {dataset.is_active && <Check className="w-4 h-4 text-brand-500" />}
                      <button
                        onClick={(e) => handleDelete(e, dataset.id)}
                        className="p-1 hover:bg-red-500/20 rounded"
                      >
                        <Trash2 className="w-3 h-3 text-foreground-muted hover:text-red-500" />
                      </button>
                    </button>
                  );
                })
              )}
            </motion.div>
          )}
        </AnimatePresence>
 
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleUpload}
          accept=".xlsx,.xls,.csv,.json,.pdf,.docx,.txt"
          className="hidden"
        />
      </div>
    );
  }
 
  // Full view (for header or standalone)
  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      {/* Main button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-surface border border-border hover:bg-surface-hover transition-all"
      >
        <div className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center">
          <FileIcon className="w-4 h-4 text-brand-500" />
        </div>
 
        <div className="flex flex-col items-start">
          <span className="text-xs text-foreground-muted">Active Dataset</span>
          <span className="text-sm font-medium text-foreground">
            {isLoading ? 'Loading...' : activeDataset?.original_filename || 'Select a dataset'}
          </span>
        </div>
 
        <ChevronDown className={`w-4 h-4 text-foreground-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
 
      {/* Error toast */}
      {error && (
        <div className="absolute top-full left-0 right-0 mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-red-500" />
          <span className="text-xs text-red-500">{error}</span>
          <button onClick={() => setError(null)} className="ml-auto">
            <X className="w-3 h-3 text-red-500" />
          </button>
        </div>
      )}
 
      {/* Dropdown */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -10, scale: 0.95 }}
            className="absolute top-full left-0 mt-2 w-80 bg-surface border border-border rounded-xl shadow-xl z-50 overflow-hidden"
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-border">
              <h3 className="text-sm font-semibold text-foreground">Datasets</h3>
              <p className="text-xs text-foreground-muted">Upload once, use everywhere</p>
            </div>
 
            {/* Upload area */}
            <div className="p-3 border-b border-border">
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 border-dashed border-border hover:border-brand-500 hover:bg-brand-500/5 transition-colors"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-5 h-5 text-brand-500 animate-spin" />
                    <span className="text-sm text-brand-500">Uploading... {uploadProgress}%</span>
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5 text-brand-500" />
                    <span className="text-sm text-foreground">Upload New Dataset</span>
                  </>
                )}
              </button>
              <p className="mt-2 text-xs text-foreground-muted text-center">
                Supports: Excel, CSV, JSON, PDF, Word, Text
              </p>
            </div>
 
            {/* Dataset list */}
            <div className="max-h-64 overflow-auto">
              {datasets.length === 0 ? (
                <div className="px-4 py-6 text-center">
                  <Database className="w-8 h-8 text-foreground-muted mx-auto mb-2" />
                  <p className="text-sm text-foreground-muted">No datasets uploaded</p>
                  <p className="text-xs text-foreground-muted mt-1">Upload a file to get started</p>
                </div>
              ) : (
                datasets.map((dataset) => {
                  const Icon = getFileIcon(dataset.file_type);
                  return (
                    <button
                      key={dataset.id}
                      onClick={() => handleSelectDataset(dataset)}
                      className={`w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-hover transition-colors ${
                        dataset.is_active ? 'bg-brand-500/5' : ''
                      }`}
                    >
                      <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                        dataset.is_active ? 'bg-brand-500/20' : 'bg-surface-hover'
                      }`}>
                        <Icon className={`w-4 h-4 ${dataset.is_active ? 'text-brand-500' : 'text-foreground-muted'}`} />
                      </div>
 
                      <div className="flex-1 text-left">
                        <p className="text-sm font-medium text-foreground truncate">
                          {dataset.original_filename}
                        </p>
                        <p className="text-xs text-foreground-muted">
                          {dataset.row_count.toLocaleString()} rows · {dataset.column_count} columns
                        </p>
                      </div>
 
                      {dataset.is_active && (
                        <Check className="w-4 h-4 text-brand-500" />
                      )}
 
                      <button
                        onClick={(e) => handleDelete(e, dataset.id)}
                        className="p-1.5 hover:bg-red-500/10 rounded-lg"
                      >
                        <Trash2 className="w-4 h-4 text-foreground-muted hover:text-red-500" />
                      </button>
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
 
      <input
        ref={fileInputRef}
        type="file"
        onChange={handleUpload}
        accept=".xlsx,.xls,.csv,.json,.pdf,.docx,.txt"
        className="hidden"
      />
    </div>
  );
};
 
export default DatasetSelector;