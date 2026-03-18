/**
 * ============================================================================
 * 📄 DOCUMENTS PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Document management page for uploading, viewing, and managing documents
 * in the RAG knowledge base.
 */

'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { api, Document } from '@/lib/api/client';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText,
  Upload,
  Trash2,
  Search,
  FileSpreadsheet,
  FileCode,
  File,
  Plus,
  Loader2,
  CheckCircle2,
  AlertCircle,
  X,
  Download,
  MoreVertical,
  Clock,
  Database,
  RefreshCw,
  FolderOpen,
} from 'lucide-react';

// =============================================================================
// FILE TYPE ICONS
// =============================================================================

const getFileIcon = (fileType: string) => {
  const type = fileType.toLowerCase();
  if (type.includes('csv') || type.includes('excel') || type.includes('xlsx') || type.includes('xls')) {
    return FileSpreadsheet;
  }
  if (type.includes('json') || type.includes('code')) {
    return FileCode;
  }
  if (type.includes('pdf') || type.includes('doc') || type.includes('txt')) {
    return FileText;
  }
  return File;
};

const getFileTypeColor = (fileType: string) => {
  const type = fileType.toLowerCase();
  if (type.includes('csv') || type.includes('excel') || type.includes('xlsx')) {
    return 'text-emerald-500 bg-emerald-500/10';
  }
  if (type.includes('json')) {
    return 'text-amber-500 bg-amber-500/10';
  }
  if (type.includes('pdf')) {
    return 'text-red-500 bg-red-500/10';
  }
  if (type.includes('doc') || type.includes('txt')) {
    return 'text-blue-500 bg-blue-500/10';
  }
  return 'text-gray-500 bg-gray-500/10';
};

// =============================================================================
// FORMAT HELPERS
// =============================================================================

const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

// =============================================================================
// UPLOAD MODAL
// =============================================================================

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (files: FileList) => void;
  isUploading: boolean;
  uploadProgress: number;
}

const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUpload,
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
    if (e.dataTransfer.files.length > 0) {
      onUpload(e.dataTransfer.files);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      onUpload(e.target.files);
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="w-full max-w-lg bg-surface rounded-2xl border border-border shadow-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-brand-600/10 flex items-center justify-center">
                <Upload className="w-5 h-5 text-brand-500" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">Upload Documents</h2>
                <p className="text-sm text-foreground-muted">Add files to your knowledge base</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-surface-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-foreground-muted" />
            </button>
          </div>

          {/* Upload area */}
          <div className="p-6">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                relative border-2 border-dashed rounded-xl p-8 text-center transition-all
                ${isDragging
                  ? 'border-brand-500 bg-brand-600/5'
                  : 'border-border hover:border-brand-500/50 hover:bg-surface-hover'
                }
                ${isUploading ? 'pointer-events-none' : 'cursor-pointer'}
              `}
              onClick={() => !isUploading && fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv,.xlsx,.xls,.json,.pdf,.txt,.doc,.docx,.md"
                onChange={handleFileSelect}
                className="hidden"
              />

              {isUploading ? (
                <div className="space-y-4">
                  <Loader2 className="w-12 h-12 text-brand-500 mx-auto animate-spin" />
                  <div>
                    <p className="text-sm font-medium text-foreground mb-2">Uploading...</p>
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
                  <div className="w-16 h-16 rounded-2xl bg-brand-600/10 flex items-center justify-center mx-auto mb-4">
                    <Upload className="w-8 h-8 text-brand-500" />
                  </div>
                  <p className="text-foreground font-medium mb-1">
                    Drop files here or click to browse
                  </p>
                  <p className="text-sm text-foreground-muted">
                    Supports CSV, Excel, JSON, PDF, TXT, DOC, and Markdown
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 pb-6">
            <p className="text-xs text-foreground-muted text-center">
              Files will be processed and added to the RAG knowledge base for intelligent querying
            </p>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// =============================================================================
// DELETE CONFIRMATION MODAL
// =============================================================================

interface DeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  documentName: string;
  isDeleting: boolean;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  documentName,
  isDeleting,
}) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className="w-full max-w-md bg-surface rounded-2xl border border-border shadow-2xl overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="p-6">
            <div className="w-12 h-12 rounded-full bg-red-500/10 flex items-center justify-center mx-auto mb-4">
              <Trash2 className="w-6 h-6 text-red-500" />
            </div>
            <h2 className="text-lg font-semibold text-foreground text-center mb-2">
              Delete Document?
            </h2>
            <p className="text-sm text-foreground-muted text-center mb-6">
              Are you sure you want to delete &ldquo;{documentName}&rdquo;? This action cannot be undone
              and will remove the document from the knowledge base.
            </p>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={isDeleting}
                className="flex-1 px-4 py-2.5 border border-border rounded-lg text-foreground hover:bg-surface-hover transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={onConfirm}
                disabled={isDeleting}
                className="flex-1 px-4 py-2.5 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// =============================================================================
// DOCUMENT CARD
// =============================================================================

interface DocumentCardProps {
  document: Document;
  onDelete: (doc: Document) => void;
}

const DocumentCard: React.FC<DocumentCardProps> = ({ document, onDelete }) => {
  const [showMenu, setShowMenu] = useState(false);
  const FileIcon = getFileIcon(document.file_type);
  const iconColorClass = getFileTypeColor(document.file_type);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="group relative bg-surface rounded-xl border border-border p-4 hover:border-brand-500/50 hover:shadow-lg transition-all"
    >
      {/* File icon and info */}
      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${iconColorClass}`}>
          <FileIcon className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-medium text-foreground truncate mb-1" title={document.filename}>
            {document.filename}
          </h3>
          <div className="flex items-center gap-3 text-xs text-foreground-muted">
            <span>{formatFileSize(document.file_size)}</span>
            <span className="w-1 h-1 rounded-full bg-foreground-muted" />
            <span>{document.chunk_count} chunks</span>
          </div>
        </div>

        {/* Actions menu */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 hover:bg-surface-hover rounded-lg transition-colors opacity-0 group-hover:opacity-100"
          >
            <MoreVertical className="w-4 h-4 text-foreground-muted" />
          </button>

          {showMenu && (
            <>
              <div
                className="fixed inset-0 z-10"
                onClick={() => setShowMenu(false)}
              />
              <div className="absolute right-0 top-full mt-1 w-40 bg-surface-elevated border border-border rounded-lg shadow-xl z-20 py-1">
                <button
                  onClick={() => {
                    setShowMenu(false);
                    onDelete(document);
                  }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-500 hover:bg-red-500/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Status and date */}
      <div className="flex items-center justify-between mt-4 pt-4 border-t border-border">
        <div className="flex items-center gap-1.5">
          {document.status === 'indexed' ? (
            <>
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span className="text-xs text-emerald-500 font-medium">Indexed</span>
            </>
          ) : document.status === 'processing' ? (
            <>
              <Loader2 className="w-4 h-4 text-amber-500 animate-spin" />
              <span className="text-xs text-amber-500 font-medium">Processing</span>
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4 text-red-500" />
              <span className="text-xs text-red-500 font-medium">Error</span>
            </>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-xs text-foreground-muted">
          <Clock className="w-3.5 h-3.5" />
          {formatDate(document.upload_date)}
        </div>
      </div>
    </motion.div>
  );
};

// =============================================================================
// EMPTY STATE
// =============================================================================

interface EmptyStateProps {
  onUpload: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({ onUpload }) => (
  <div className="flex flex-col items-center justify-center py-16 text-center">
    <div className="w-20 h-20 rounded-2xl bg-brand-600/10 flex items-center justify-center mb-6">
      <FolderOpen className="w-10 h-10 text-brand-500" />
    </div>
    <h2 className="text-xl font-semibold text-foreground mb-2">No documents yet</h2>
    <p className="text-foreground-muted max-w-md mb-8">
      Upload documents to build your knowledge base. The AI will use these documents
      to provide intelligent answers to your questions.
    </p>
    <button
      onClick={onUpload}
      className="flex items-center gap-2 px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors"
    >
      <Upload className="w-5 h-5" />
      Upload Your First Document
    </button>
  </div>
);

// =============================================================================
// MAIN DOCUMENTS PAGE
// =============================================================================

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [filteredDocuments, setFilteredDocuments] = useState<Document[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal states
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);

  // Upload state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  // Delete state
  const [isDeleting, setIsDeleting] = useState(false);

  // Fetch documents
  const fetchDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.document.list();
      setDocuments(response.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      setError('Failed to load documents. Please check if the backend is running.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Load documents on mount
  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  // Filter documents based on search
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredDocuments(documents);
    } else {
      const query = searchQuery.toLowerCase();
      setFilteredDocuments(
        documents.filter(
          (doc) =>
            doc.filename.toLowerCase().includes(query) ||
            doc.file_type.toLowerCase().includes(query)
        )
      );
    }
  }, [searchQuery, documents]);

  // Handle upload
  const handleUpload = useCallback(async (files: FileList) => {
    setIsUploading(true);
    setUploadProgress(0);

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        await api.document.upload(file, (progress) => {
          const overallProgress = ((i + progress / 100) / files.length) * 100;
          setUploadProgress(Math.round(overallProgress));
        });
      }
      setShowUploadModal(false);
      fetchDocuments();
    } catch (err) {
      console.error('Upload failed:', err);
      setError('Failed to upload document. Please try again.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [fetchDocuments]);

  // Handle delete
  const handleDelete = useCallback(async () => {
    if (!selectedDocument) return;

    setIsDeleting(true);
    try {
      await api.document.delete(selectedDocument.doc_id);
      setShowDeleteModal(false);
      setSelectedDocument(null);
      fetchDocuments();
    } catch (err) {
      console.error('Delete failed:', err);
      setError('Failed to delete document. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  }, [selectedDocument, fetchDocuments]);

  // Open delete confirmation
  const openDeleteModal = useCallback((doc: Document) => {
    setSelectedDocument(doc);
    setShowDeleteModal(true);
  }, []);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-background">
        <div className="max-w-6xl mx-auto p-8">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-foreground mb-2">Documents</h1>
              <p className="text-foreground-secondary">
                Manage your knowledge base documents
              </p>
            </div>
            <button
              onClick={() => setShowUploadModal(true)}
              className="flex items-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors"
            >
              <Plus className="w-5 h-5" />
              Upload Document
            </button>
          </div>

          {/* Search and stats bar */}
          <div className="flex items-center gap-4 mb-6">
            {/* Search */}
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-foreground-muted" />
              <input
                type="text"
                placeholder="Search documents..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-surface border border-border rounded-xl text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 focus:border-brand-600"
              />
            </div>

            {/* Stats */}
            <div className="flex items-center gap-3 px-4 py-2 bg-surface border border-border rounded-xl">
              <Database className="w-4 h-4 text-brand-500" />
              <span className="text-sm text-foreground">
                <span className="font-semibold">{documents.length}</span> documents
              </span>
              <span className="w-1 h-1 rounded-full bg-foreground-muted" />
              <span className="text-sm text-foreground">
                <span className="font-semibold">
                  {documents.reduce((acc, doc) => acc + doc.chunk_count, 0)}
                </span> chunks
              </span>
            </div>

            {/* Refresh button */}
            <button
              onClick={fetchDocuments}
              disabled={isLoading}
              className="p-2.5 hover:bg-surface-hover border border-border rounded-xl transition-colors disabled:opacity-50"
              title="Refresh"
            >
              <RefreshCw className={`w-5 h-5 text-foreground-muted ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
              <p className="text-sm text-red-500">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto p-1 hover:bg-red-500/20 rounded transition-colors"
              >
                <X className="w-4 h-4 text-red-500" />
              </button>
            </div>
          )}

          {/* Content */}
          {isLoading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
            </div>
          ) : filteredDocuments.length === 0 && searchQuery === '' ? (
            <EmptyState onUpload={() => setShowUploadModal(true)} />
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-16">
              <Search className="w-12 h-12 text-foreground-muted mx-auto mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">No results found</h3>
              <p className="text-foreground-muted">
                No documents match &ldquo;{searchQuery}&rdquo;
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDocuments.map((doc) => (
                <DocumentCard
                  key={doc.doc_id}
                  document={doc}
                  onDelete={openDeleteModal}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        onUpload={handleUpload}
        isUploading={isUploading}
        uploadProgress={uploadProgress}
      />

      <DeleteModal
        isOpen={showDeleteModal}
        onClose={() => {
          setShowDeleteModal(false);
          setSelectedDocument(null);
        }}
        onConfirm={handleDelete}
        documentName={selectedDocument?.filename || ''}
        isDeleting={isDeleting}
      />
    </div>
  );
}
