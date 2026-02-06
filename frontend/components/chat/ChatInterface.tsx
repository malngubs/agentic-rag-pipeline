/**
 * ============================================================================
 * 💬 CHAT INTERFACE - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * The main conversational interface for the BI platform.
 * 
 * FIXED:
 * - Properly connects to /ws/chat/stream WebSocket
 * - Falls back to REST API (/api/chat) if WebSocket fails
 * - Handles streaming responses correctly
 * - Shows source citations from RAG
 * 
 * Features:
 * - Natural language queries with RAG
 * - Real-time streaming responses
 * - File upload with drag-and-drop
 * - Rich message formatting
 * - Source citations display
 */

'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  Send,
  Paperclip,
  X,
  Loader2,
  BrainCircuit,
  Wand2,
  Lightbulb,
  BarChart3,
  FileSpreadsheet,
  MessageSquare,
  ArrowDown,
  CheckCircle2,
  AlertCircle,
  FileText,
  RefreshCw,
} from 'lucide-react';
import { api, ChatWebSocket, ChatResponse, DatasetUploadResponse } from '@/lib/api/client';
import {
  ChartWidget,
  DashboardWidget,
  KPICard,
  DataTable
} from '@/components/visualizations';
import { DocumentPreview } from './DocumentPreview';

// =============================================================================
// TYPES
// =============================================================================

interface UploadedDocument {
  filename: string;
  fileSize: number;
  fileType: string;
  rowCount?: number;
  columnCount?: number;
  columns?: any[];
  vectorChunks?: number;
  isActive?: boolean;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  status: 'sending' | 'streaming' | 'complete' | 'error';
  sources?: Array<{
    document_name: string;
    chunk_text: string;
    similarity_score: number;
  }>;
  visualizations?: Array<{
    type: 'chart' | 'dashboard' | 'table' | 'kpi';
    data: any;
    title?: string;
    description?: string;
  }>;
  uploadedDocument?: UploadedDocument;
  executionTime?: number;
  error?: string;
}

// =============================================================================
// MESSAGE COMPONENT
// =============================================================================

interface MessageProps {
  message: ChatMessage;
  isLast: boolean;
}

const Message: React.FC<MessageProps> = ({ message, isLast }) => {
  const isUser = message.role === 'user';
  const isStreaming = message.status === 'streaming';
  const [showSources, setShowSources] = useState(false);
  
  return (
    <div
      className={`flex gap-4 animate-slide-in ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div
        className={`
          flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center
          ${isUser 
            ? 'glossy-button' 
            : 'glass border border-white/10'
          }
        `}
      >
        {isUser ? (
          <span className="text-sm font-semibold text-white">U</span>
        ) : (
          <BrainCircuit className="w-4 h-4 text-[var(--color-brand-500)]" />
        )}
      </div>
      
      {/* Message content */}
      <div
        className={`
          max-w-[75%] rounded-2xl px-4 py-3 transition-all duration-200
          ${isUser
            ? 'chat-message-user'
            : 'chat-message-assistant glossy-card'
          }
        `}
      >
        {/* Main content */}
        <div className="chat-content">
          {message.content || (isStreaming && (
            <span className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </span>
          ))}
          {isStreaming && message.content && (
            <span className="inline-block w-2 h-5 bg-[var(--color-brand-500)] ml-1 animate-blink rounded-sm" />
          )}
        </div>
        
        {/* Visualizations - render charts, dashboards, tables inline */}
        {message.visualizations && message.visualizations.length > 0 && (
          <div className="mt-4 space-y-4">
            {message.visualizations.map((viz, index) => {
              switch (viz.type) {
                case 'chart':
                  return (
                    <ChartWidget
                      key={index}
                      chartData={viz.data}
                      title={viz.title}
                      description={viz.description}
                    />
                  );
                case 'dashboard':
                  return (
                    <DashboardWidget
                      key={index}
                      dashboard={viz.data}
                    />
                  );
                case 'table':
                  return (
                    <DataTable
                      key={index}
                      data={viz.data}
                      title={viz.title}
                    />
                  );
                case 'kpi':
                  return (
                    <KPICard
                      key={index}
                      {...viz.data}
                    />
                  );
                default:
                  return null;
              }
            })}
          </div>
        )}

        {/* Document Preview - show after upload */}
        {message.uploadedDocument && (
          <div className="mt-4">
            <DocumentPreview
              filename={message.uploadedDocument.filename}
              fileSize={message.uploadedDocument.fileSize}
              fileType={message.uploadedDocument.fileType}
              rowCount={message.uploadedDocument.rowCount}
              columnCount={message.uploadedDocument.columnCount}
              columns={message.uploadedDocument.columns}
              vectorChunks={message.uploadedDocument.vectorChunks}
              isActive={message.uploadedDocument.isActive}
            />
          </div>
        )}

        {/* Sources - show citations from RAG */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-white/10">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-2 text-sm text-[var(--color-foreground-muted)] hover:text-[var(--color-foreground)] transition-colors"
            >
              <FileText className="w-4 h-4" />
              <span>{message.sources.length} source{message.sources.length > 1 ? 's' : ''}</span>
              <span className={`transform transition-transform ${showSources ? 'rotate-180' : ''}`}>▼</span>
            </button>

            {showSources && (
              <div className="mt-2 space-y-2">
                {message.sources.map((source, index) => (
                  <div
                    key={index}
                    className="p-3 bg-[var(--color-surface-muted)] rounded-lg border border-[var(--color-border)]"
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <FileSpreadsheet className="w-4 h-4 text-[var(--color-brand-500)]" />
                      <span className="text-sm font-medium text-[var(--color-foreground)]">
                        {source.document_name}
                      </span>
                      <span className="text-xs text-[var(--color-foreground-subtle)] ml-auto">
                        {(source.similarity_score * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <p className="text-xs text-[var(--color-foreground-muted)] line-clamp-2">
                      {source.chunk_text}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
        
        {/* Metadata */}
        {message.status === 'complete' && message.executionTime && (
          <div className="mt-2 flex items-center gap-2 text-xs text-[var(--color-foreground-subtle)]">
            <CheckCircle2 className="w-3 h-3 text-[var(--color-success)]" />
            <span>Completed in {message.executionTime.toFixed(2)}s</span>
          </div>
        )}
        
        {/* Error */}
        {message.error && (
          <div className="mt-2 flex items-center gap-2 text-sm text-[var(--color-error)]">
            <AlertCircle className="w-4 h-4" />
            <span>{message.error}</span>
          </div>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// FILE PREVIEW
// =============================================================================

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
  uploadProgress?: number;
}

const FilePreview: React.FC<FilePreviewProps> = ({ file, onRemove, uploadProgress }) => {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  return (
    <div className="flex items-center gap-3 p-3 glass rounded-lg">
      <FileSpreadsheet className="w-5 h-5 text-[var(--color-success)]" />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-[var(--color-foreground)] truncate">
          {file.name}
        </div>
        <div className="text-xs text-[var(--color-foreground-muted)]">
          {formatSize(file.size)}
        </div>
        {uploadProgress !== undefined && uploadProgress < 100 && (
          <div className="mt-1 h-1 bg-[var(--color-surface-muted)] rounded-full overflow-hidden">
            <div 
              className="h-full bg-[var(--color-brand-600)] transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        )}
      </div>
      <button
        onClick={onRemove}
        className="p-1.5 hover:bg-[var(--color-surface-active)] rounded-lg transition-colors"
      >
        <X className="w-4 h-4 text-[var(--color-foreground-muted)]" />
      </button>
    </div>
  );
};

// =============================================================================
// CHAT INPUT
// =============================================================================

interface ChatInputProps {
  onSend: (message: string, file?: File) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, isLoading, disabled }) => {
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);
  
  // Handle submit
  const handleSubmit = useCallback(() => {
    if ((input.trim() || selectedFile) && !isLoading && !disabled) {
      onSend(input.trim(), selectedFile || undefined);
      setInput('');
      setSelectedFile(null);
    }
  }, [input, selectedFile, isLoading, disabled, onSend]);
  
  // Handle key press
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };
  
  // Handle file selection
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
    e.target.value = '';
  };
  
  // Handle drag and drop
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
    if (file) {
      setSelectedFile(file);
    }
  };
  
  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`
        relative rounded-2xl transition-all duration-200 glossy-card
        ${isDragging
          ? 'border-[var(--color-brand-500)] bg-[var(--color-brand-600)]/5'
          : 'border-[var(--color-border)]'
        }
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      {/* Drag overlay */}
      {isDragging && (
        <div className="absolute inset-0 flex items-center justify-center glass-brand rounded-2xl z-10">
          <div className="text-[var(--color-brand-500)] font-medium">
            Drop file here
          </div>
        </div>
      )}
      
      {/* File preview */}
      {selectedFile && (
        <div className="px-4 pt-3">
          <FilePreview
            file={selectedFile}
            onRemove={() => setSelectedFile(null)}
          />
        </div>
      )}
      
      {/* Input area */}
      <div className="flex items-end gap-2 p-3">
        {/* File upload button */}
        <button
          onClick={() => fileInputRef.current?.click()}
          className="flex-shrink-0 p-2.5 hover:bg-[var(--color-surface-hover)] rounded-xl transition-colors"
          title="Attach file"
        >
          <Paperclip className="w-5 h-5 text-[var(--color-foreground-muted)]" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".csv,.xlsx,.xls,.json,.pdf,.txt,.doc,.docx"
          className="hidden"
        />
        
        {/* Text input */}
        <textarea
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask me anything about your data..."
          rows={1}
          className="flex-1 resize-none bg-transparent text-[var(--color-foreground)] placeholder:text-[var(--color-foreground-subtle)] focus:outline-none text-[15px] leading-relaxed max-h-48 scrollbar-thin py-2"
        />
        
        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={(!input.trim() && !selectedFile) || isLoading}
          className={`
            flex-shrink-0 p-2.5 rounded-xl transition-all duration-200
            ${input.trim() || selectedFile
              ? 'glossy-button text-white'
              : 'bg-[var(--color-surface-hover)] text-[var(--color-foreground-muted)]'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <Send className="w-5 h-5" />
          )}
        </button>
      </div>
      
      {/* Keyboard hint */}
      <div className="px-4 pb-3 text-xs text-[var(--color-foreground-subtle)]">
        Press <kbd className="px-1.5 py-0.5 bg-[var(--color-surface-muted)] rounded text-[var(--color-foreground-muted)] font-mono">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-[var(--color-surface-muted)] rounded text-[var(--color-foreground-muted)] font-mono">Shift + Enter</kbd> for new line
      </div>
    </div>
  );
};

// =============================================================================
// EMPTY STATE
// =============================================================================

interface EmptyStateProps {
  onSuggestionClick: (text: string) => void;
  onUploadClick: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({ onSuggestionClick, onUploadClick }) => {
  const primarySuggestions = [
    {
      icon: FileSpreadsheet,
      title: 'Upload your data',
      description: 'Drag & drop CSV, Excel, PDF, or JSON files',
      action: 'upload' as const,
    },
    {
      icon: MessageSquare,
      title: 'Ask questions',
      description: '"Show me sales trends by region"',
      query: 'Show me sales trends by region',
    },
    {
      icon: BarChart3,
      title: 'Create visualizations',
      description: '"Create a dashboard with key metrics"',
      query: 'Create a dashboard with key metrics',
    },
    {
      icon: Lightbulb,
      title: 'Get insights',
      description: '"What are the key insights from this data?"',
      query: 'What are the key insights from this data?',
    },
  ];

  const analysisSuggestions = [
    {
      title: 'Forecast sales for the next 12 months',
      icon: '📈',
    },
    {
      title: 'Run correlation analysis on my data',
      icon: '🔗',
    },
    {
      title: 'Perform statistical hypothesis testing',
      icon: '🧪',
    },
    {
      title: 'Profile my data and show quality metrics',
      icon: '📊',
    },
    {
      title: 'Identify anomalies and outliers',
      icon: '🎯',
    },
    {
      title: 'Generate a financial summary report',
      icon: '💰',
    },
  ];

  const handleClick = (suggestion: typeof primarySuggestions[0]) => {
    if ('action' in suggestion && suggestion.action === 'upload') {
      onUploadClick();
    } else if ('query' in suggestion && suggestion.query) {
      onSuggestionClick(suggestion.query);
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      {/* Logo/Title */}
      <div className="text-center mb-10 animate-fade-in">
        <div className="w-20 h-20 rounded-2xl glass-brand flex items-center justify-center mx-auto mb-6 card-glow">
          <BrainCircuit className="w-10 h-10 text-[var(--color-brand-500)]" />
        </div>
        <h1 className="text-3xl font-bold text-[var(--color-foreground)] mb-3">
          Macrocomm BI Assistant
        </h1>
        <p className="text-[var(--color-foreground-muted)] max-w-lg text-lg">
          Your AI-powered data analyst. Upload data, ask questions, create forecasts, and get intelligent insights.
        </p>
      </div>

      {/* Primary suggestion cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full mb-8">
        {primarySuggestions.map((suggestion, index) => (
          <div
            key={suggestion.title}
            onClick={() => handleClick(suggestion)}
            className="card-interactive card-glow group animate-slide-in cursor-pointer"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-xl glass-brand group-hover:scale-110 transition-transform">
                <suggestion.icon className="w-5 h-5 text-[var(--color-brand-500)]" />
              </div>
              <div>
                <div className="font-semibold text-[var(--color-foreground)] mb-1">
                  {suggestion.title}
                </div>
                <div className="text-sm text-[var(--color-foreground-muted)]">
                  {suggestion.description}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Analysis quick actions */}
      <div className="max-w-2xl w-full">
        <p className="text-sm text-[var(--color-foreground-muted)] mb-3 text-center">
          Try asking for advanced analysis:
        </p>
        <div className="flex flex-wrap gap-2 justify-center">
          {analysisSuggestions.map((item, index) => (
            <button
              key={index}
              onClick={() => onSuggestionClick(item.title)}
              className="px-3 py-2 text-sm bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg hover:border-[var(--color-brand-500)] hover:bg-[var(--color-surface-hover)] transition-all text-[var(--color-foreground-muted)] hover:text-[var(--color-foreground)]"
            >
              <span className="mr-2">{item.icon}</span>
              {item.title}
            </button>
          ))}
        </div>
      </div>

      {/* Analysis workspace link */}
      <div className="mt-8 text-center">
        <a
          href="/analysis"
          className="inline-flex items-center gap-2 text-sm text-[var(--color-brand-500)] hover:text-[var(--color-brand-400)] transition-colors"
        >
          <span>Or use the advanced Analysis Workspace</span>
          <span>→</span>
        </a>
      </div>
    </div>
  );
};

// =============================================================================
// CONNECTION STATUS
// =============================================================================

interface ConnectionStatusProps {
  isConnected: boolean;
  onReconnect: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected, onReconnect }) => {
  if (isConnected) {
    return (
      <div className="flex items-center gap-2 text-sm text-[var(--color-success)]">
        <span className="status-dot status-dot-online" />
        <span>Connected</span>
      </div>
    );
  }
  
  return (
    <button
      onClick={onReconnect}
      className="flex items-center gap-2 text-sm text-[var(--color-warning)] hover:text-[var(--color-foreground)] transition-colors"
    >
      <span className="status-dot status-dot-busy" />
      <span>Reconnect</span>
      <RefreshCw className="w-3 h-3" />
    </button>
  );
};

// =============================================================================
// MAIN CHAT INTERFACE
// =============================================================================

export const ChatInterface: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<ChatWebSocket | null>(null);
  const uploadInputRef = useRef<HTMLInputElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [conversationId, setConversationId] = useState<string | undefined>();
  
  // Scroll to bottom
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    messagesEndRef.current?.scrollIntoView({ behavior });
  }, []);
  
  // Auto-scroll on new messages
  useEffect(() => {
    if (messages.length > 0) {
      scrollToBottom();
    }
  }, [messages.length, scrollToBottom]);
  
  // Check if scrolled up
  const handleScroll = useCallback(() => {
    if (messagesContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = messagesContainerRef.current;
      const isScrolledUp = scrollHeight - scrollTop - clientHeight > 100;
      setShowScrollButton(isScrolledUp);
    }
  }, []);
  
  // Initialize WebSocket connection
  const connectWebSocket = useCallback(() => {
    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.disconnect();
    }
    
    const ws = new ChatWebSocket(
      // On stream chunk
      (chunk) => {
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.status === 'streaming') {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, content: lastMessage.content + chunk }
            ];
          }
          return prev;
        });
      },
      // On complete
      (response) => {
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            // Parse visualizations from response
            const visualizations: Array<{
              type: 'chart' | 'dashboard' | 'table' | 'kpi';
              data: any;
              title?: string;
              description?: string;
            }> = [];

            // Check for chart data
            if (response.chart) {
              visualizations.push({
                type: 'chart',
                data: response.chart,
                title: response.chart_title,
                description: response.chart_description
              });
            }

            // Check for dashboard data
            if (response.dashboard) {
              visualizations.push({
                type: 'dashboard',
                data: response.dashboard
              });
            }

            // Check for table data
            if (response.table) {
              visualizations.push({
                type: 'table',
                data: response.table,
                title: response.table_title
              });
            }

            // Check for KPI data
            if (response.kpi) {
              visualizations.push({
                type: 'kpi',
                data: response.kpi
              });
            }

            return [
              ...prev.slice(0, -1),
              {
                ...lastMessage,
                content: response.response || lastMessage.content,
                status: 'complete',
                sources: response.sources,
                visualizations: visualizations.length > 0 ? visualizations : undefined,
                executionTime: response.response_time,
              }
            ];
          }
          return prev;
        });
        setConversationId(response.conversation_id);
        setIsLoading(false);
      },
      // On error
      (error) => {
        console.error('WebSocket error:', error);
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage && lastMessage.role === 'assistant' && lastMessage.status === 'streaming') {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, status: 'error', error: error.message }
            ];
          }
          return prev;
        });
        setIsLoading(false);
        setIsConnected(false);
      },
      conversationId
    );
    
    ws.connect()
      .then(() => {
        setIsConnected(true);
        wsRef.current = ws;
      })
      .catch((err) => {
        console.error('Failed to connect WebSocket:', err);
        setIsConnected(false);
      });
  }, [conversationId]);
  
  // Connect on mount
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.disconnect();
      }
    };
  }, []);
  
  // Handle send message
  const handleSend = useCallback(async (content: string, file?: File) => {
    try {
      setIsLoading(true);
      
      // Handle file upload first
      if (file) {
        const userMessageId = `user-${Date.now()}`;
        setMessages(prev => [...prev, {
          id: userMessageId,
          role: 'user',
          content: `📎 Uploading: ${file.name}`,
          timestamp: new Date().toISOString(),
          status: 'complete',
        }]);

        try {
          // Use dataset API for full metadata including preview data
          const uploadResult = await api.dataset.upload(file);
          setMessages(prev => [...prev, {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: `✅ Successfully uploaded "${file.name}". The document has been processed and is ready for analysis.`,
            timestamp: new Date().toISOString(),
            status: 'complete',
            uploadedDocument: {
              filename: uploadResult.filename,
              fileSize: uploadResult.file_size,
              fileType: uploadResult.file_type,
              rowCount: uploadResult.row_count,
              columnCount: uploadResult.column_count,
              columns: uploadResult.columns,
              vectorChunks: uploadResult.vector_chunks,
              isActive: uploadResult.is_active,
            },
          }]);
        } catch (uploadError) {
          setMessages(prev => [...prev, {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: 'Failed to upload the file. Please try again.',
            timestamp: new Date().toISOString(),
            status: 'error',
            error: uploadError instanceof Error ? uploadError.message : 'Upload failed',
          }]);
          setIsLoading(false);
          return;
        }
      }
      
      // Send message if there's content
      if (content) {
        // Add user message
        const userMessageId = `user-${Date.now()}`;
        setMessages(prev => [...prev, {
          id: userMessageId,
          role: 'user',
          content,
          timestamp: new Date().toISOString(),
          status: 'complete',
        }]);
        
        // Add streaming assistant message placeholder
        const assistantMessageId = `assistant-${Date.now()}`;
        setMessages(prev => [...prev, {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          status: 'streaming',
        }]);
        
        // Try WebSocket first, fallback to REST API
        if (wsRef.current && wsRef.current.isConnected()) {
          wsRef.current.send(content);
        } else {
          // Fallback to REST API (/api/chat)
          try {
            const response = await api.chat.send(content, conversationId);
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage && lastMessage.id === assistantMessageId) {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    content: response.response,
                    status: 'complete',
                    sources: response.sources,
                    executionTime: response.response_time,
                  }
                ];
              }
              return prev;
            });
            setConversationId(response.conversation_id);
            setIsLoading(false);
          } catch (error) {
            setMessages(prev => {
              const lastMessage = prev[prev.length - 1];
              if (lastMessage && lastMessage.id === assistantMessageId) {
                return [
                  ...prev.slice(0, -1),
                  {
                    ...lastMessage,
                    status: 'error',
                    error: error instanceof Error ? error.message : 'Request failed',
                  }
                ];
              }
              return prev;
            });
            setIsLoading(false);
          }
        }
      } else {
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Send error:', error);
      setIsLoading(false);
    }
  }, [conversationId]);
  
  // Handle suggestion click
  const handleSuggestionClick = useCallback((query: string) => {
    handleSend(query);
  }, [handleSend]);

  // Handle upload click from empty state
  const handleUploadClick = useCallback(() => {
    uploadInputRef.current?.click();
  }, []);

  // Handle file selected from empty state upload
  const handleUploadFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleSend('', file);
    }
    e.target.value = '';
  }, [handleSend]);

  return (
    <div className="flex flex-col h-full">
      {/* Hidden file input for empty state upload */}
      <input
        ref={uploadInputRef}
        type="file"
        onChange={handleUploadFileSelect}
        accept=".csv,.xlsx,.xls,.json,.pdf,.txt,.doc,.docx"
        className="hidden"
      />

      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--color-border)] glass">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl glass-brand flex items-center justify-center">
            <Wand2 className="w-5 h-5 text-[var(--color-brand-500)]" />
          </div>
          <div>
            <h2 className="font-semibold text-[var(--color-foreground)]">AI Assistant</h2>
            <p className="text-sm text-[var(--color-foreground-muted)]">
              Ask questions about your data in natural language
            </p>
          </div>
        </div>
        <ConnectionStatus isConnected={isConnected} onReconnect={connectWebSocket} />
      </div>
      
      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto scrollbar-thin"
      >
        {messages.length === 0 ? (
          <EmptyState
            onSuggestionClick={handleSuggestionClick}
            onUploadClick={handleUploadClick}
          />
        ) : (
          <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
            {messages.map((message, index) => (
              <Message
                key={message.id}
                message={message}
                isLast={index === messages.length - 1}
              />
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>
      
      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={() => scrollToBottom()}
          className="absolute bottom-32 right-8 p-3 glass rounded-full shadow-lg hover:bg-[var(--color-surface-hover)] transition-colors animate-fade-in"
        >
          <ArrowDown className="w-5 h-5 text-[var(--color-foreground)]" />
        </button>
      )}
      
      {/* Input area */}
      <div className="border-t border-[var(--color-border)] glass">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;