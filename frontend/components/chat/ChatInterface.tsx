/**
 * ============================================================================
 * 💬 CHAT INTERFACE - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * The main conversational interface for the BI platform.
 * Features:
 * - Natural language queries
 * - Real-time streaming responses
 * - File upload with drag-and-drop
 * - Rich message formatting (markdown, code, charts)
 * - Keyboard shortcuts
 */

'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Paperclip,
  X,
  Loader2,
  Sparkles,
  BarChart3,
  FileSpreadsheet,
  MessageSquare,
  ArrowDown,
  Mic,
  StopCircle,
} from 'lucide-react';
import { useChatStore, useSessionStore, useUIStore, toast } from '@/lib/stores';
import { api } from '@/lib/api/client';
import type { ChatMessage, QueryResult, UploadedFile } from '@/types';

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
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
      className={`flex gap-4 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
    >
      {/* Avatar */}
      <div
        className={`
          flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser 
            ? 'bg-brand-600 text-white' 
            : 'bg-surface-hover border border-border'
          }
        `}
      >
        {isUser ? (
          <span className="text-sm font-medium">U</span>
        ) : (
          <Sparkles className="w-4 h-4 text-brand-500" />
        )}
      </div>
      
      {/* Message content */}
      <div
        className={`
          max-w-[75%] rounded-2xl px-4 py-3
          ${isUser
            ? 'bg-brand-600/10 border border-brand-600/20 rounded-br-md'
            : 'bg-surface border border-border rounded-bl-md'
          }
        `}
      >
        {/* Main content */}
        <div className="chat-content">
          {message.content}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-brand-500 ml-1 animate-blink" />
          )}
        </div>
        
        {/* Charts */}
        {message.charts && message.charts.length > 0 && (
          <div className="mt-4 space-y-3">
            {message.charts.map((chart, index) => (
              <div
                key={chart.id || index}
                className="bg-surface-muted rounded-lg p-4 border border-border"
              >
                <div className="flex items-center gap-2 mb-2">
                  <BarChart3 className="w-4 h-4 text-brand-500" />
                  <span className="text-sm font-medium text-foreground">
                    {chart.title || `Chart ${index + 1}`}
                  </span>
                </div>
                {chart.html ? (
                  <div
                    className="plotly-chart-container"
                    dangerouslySetInnerHTML={{ __html: chart.html }}
                  />
                ) : (
                  <div className="h-48 flex items-center justify-center text-foreground-muted">
                    Chart visualization
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        
        {/* Insights */}
        {message.insights && message.insights.length > 0 && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-500" />
              <span className="text-sm font-medium text-foreground">
                Key Insights
              </span>
            </div>
            <ul className="space-y-1">
              {message.insights.map((insight, index) => (
                <li
                  key={index}
                  className="text-sm text-foreground-secondary flex items-start gap-2"
                >
                  <span className="text-brand-500 mt-1">•</span>
                  <span>{insight}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        
        {/* Metadata */}
        {message.status === 'complete' && message.executionTime && (
          <div className="mt-2 text-xs text-foreground-muted">
            Completed in {message.executionTime.toFixed(2)}s
          </div>
        )}
        
        {/* Error */}
        {message.error && (
          <div className="mt-2 text-sm text-error">
            {message.error}
          </div>
        )}
      </div>
    </motion.div>
  );
};

// =============================================================================
// FILE UPLOAD PREVIEW
// =============================================================================

interface FilePreviewProps {
  file: File;
  onRemove: () => void;
}

const FilePreview: React.FC<FilePreviewProps> = ({ file, onRemove }) => {
  const getFileIcon = () => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'xlsx':
      case 'xls':
      case 'csv':
        return <FileSpreadsheet className="w-5 h-5 text-success" />;
      default:
        return <FileSpreadsheet className="w-5 h-5 text-foreground-muted" />;
    }
  };
  
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };
  
  return (
    <div className="flex items-center gap-3 bg-surface-hover rounded-lg px-3 py-2 border border-border">
      {getFileIcon()}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-foreground truncate">
          {file.name}
        </div>
        <div className="text-xs text-foreground-muted">
          {formatSize(file.size)}
        </div>
      </div>
      <button
        onClick={onRemove}
        className="p-1 hover:bg-surface-active rounded transition-colors"
      >
        <X className="w-4 h-4 text-foreground-muted" />
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
        relative rounded-2xl border transition-all duration-200
        ${isDragging
          ? 'border-brand-500 bg-brand-600/5'
          : 'border-border bg-surface hover:border-border-light'
        }
        ${disabled ? 'opacity-50 pointer-events-none' : ''}
      `}
    >
      {/* Drag overlay */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 flex items-center justify-center bg-brand-600/10 rounded-2xl z-10"
          >
            <div className="text-brand-500 font-medium">
              Drop file here
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
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
          className="flex-shrink-0 p-2 hover:bg-surface-hover rounded-lg transition-colors"
          title="Attach file"
        >
          <Paperclip className="w-5 h-5 text-foreground-muted" />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleFileSelect}
          accept=".csv,.xlsx,.xls,.json,.pdf,.txt"
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
          className={`
            flex-1 resize-none bg-transparent text-foreground placeholder:text-foreground-muted
            focus:outline-none text-sm leading-relaxed max-h-48 scrollbar-thin
          `}
        />
        
        {/* Send button */}
        <button
          onClick={handleSubmit}
          disabled={(!input.trim() && !selectedFile) || isLoading}
          className={`
            flex-shrink-0 p-2 rounded-lg transition-all duration-200
            ${input.trim() || selectedFile
              ? 'bg-brand-600 text-white hover:bg-brand-500'
              : 'bg-surface-hover text-foreground-muted'
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
      <div className="px-4 pb-2 text-xs text-foreground-muted">
        Press <kbd className="px-1.5 py-0.5 bg-surface-muted rounded text-foreground-muted">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-surface-muted rounded text-foreground-muted">Shift + Enter</kbd> for new line
      </div>
    </div>
  );
};

// =============================================================================
// EMPTY STATE
// =============================================================================

const EmptyState: React.FC = () => {
  const suggestions = [
    {
      icon: FileSpreadsheet,
      title: 'Upload your data',
      description: 'Drag & drop CSV, Excel, or other data files',
    },
    {
      icon: MessageSquare,
      title: 'Ask questions',
      description: '"Show me sales trends by region"',
    },
    {
      icon: BarChart3,
      title: 'Create visualizations',
      description: '"Create a dashboard with key metrics"',
    },
    {
      icon: Sparkles,
      title: 'Get insights',
      description: '"What are the key insights from this data?"',
    },
  ];
  
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      {/* Logo/Title */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center mb-12"
      >
        <div className="w-16 h-16 rounded-2xl bg-brand-600/10 border border-brand-600/20 flex items-center justify-center mx-auto mb-4">
          <Sparkles className="w-8 h-8 text-brand-500" />
        </div>
        <h1 className="text-2xl font-display font-bold text-foreground mb-2">
          Macrocomm BI Assistant
        </h1>
        <p className="text-foreground-secondary max-w-md">
          Ask questions in natural language, upload your data, and get AI-powered insights and visualizations.
        </p>
      </motion.div>
      
      {/* Suggestion cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl w-full">
        {suggestions.map((suggestion, index) => (
          <motion.div
            key={suggestion.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            className="card-interactive cursor-pointer group"
          >
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-brand-600/10 group-hover:bg-brand-600/20 transition-colors">
                <suggestion.icon className="w-5 h-5 text-brand-500" />
              </div>
              <div>
                <div className="font-medium text-foreground mb-1">
                  {suggestion.title}
                </div>
                <div className="text-sm text-foreground-muted">
                  {suggestion.description}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// =============================================================================
// MAIN CHAT INTERFACE
// =============================================================================

export const ChatInterface: React.FC = () => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [showScrollButton, setShowScrollButton] = useState(false);
  
  // Store hooks
  const {
    messages,
    isLoading,
    isStreaming,
    addMessage,
    updateMessage,
    setLoading,
    setStreaming,
    appendToLastMessage,
    finalizeLastMessage,
  } = useChatStore();
  
  const { currentSession, setCurrentSession } = useSessionStore();
  
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
  
  // Create session if needed
  const ensureSession = useCallback(async (): Promise<string> => {
    if (currentSession?.id) {
      return currentSession.id;
    }
    
    try {
      const response = await api.session.create();
      setCurrentSession({
        id: response.sessionId,
        createdAt: response.createdAt,
        lastActive: response.createdAt,
        status: response.status,
      });
      return response.sessionId;
    } catch (error) {
      toast.error('Failed to create session', 'Please try again');
      throw error;
    }
  }, [currentSession, setCurrentSession]);
  
  // Handle send message
  const handleSend = useCallback(async (content: string, file?: File) => {
    try {
      setLoading(true);
      
      // Ensure we have a session
      const sessionId = await ensureSession();
      
      // Add user message
      const userMessageId = `user-${Date.now()}`;
      addMessage({
        id: userMessageId,
        role: 'user',
        content: file ? `[Uploaded: ${file.name}]\n\n${content || 'Analyze this file'}` : content,
        timestamp: new Date().toISOString(),
        status: 'sent',
      });
      
      // Upload file if provided
      if (file) {
        try {
          const uploadResult = await api.session.uploadFile(sessionId, file);
          
          // Add assistant message for upload
          addMessage({
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: uploadResult.response,
            timestamp: new Date().toISOString(),
            status: 'complete',
            charts: uploadResult.charts,
            insights: uploadResult.insights,
            executionTime: uploadResult.executionTime,
          });
        } catch (error) {
          addMessage({
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: 'Failed to process the uploaded file. Please try again.',
            timestamp: new Date().toISOString(),
            status: 'error',
            error: error instanceof Error ? error.message : 'Upload failed',
          });
          return;
        }
      }
      
      // Send query if there's content
      if (content) {
        // Add streaming assistant message
        const assistantMessageId = `assistant-${Date.now()}`;
        addMessage({
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          status: 'streaming',
        });
        
        setStreaming(true);
        
        try {
          const result = await api.session.query(sessionId, content);
          
          // Update with result
          updateMessage(assistantMessageId, {
            content: result.response,
            status: 'complete',
            intent: result.intent,
            charts: result.charts,
            dashboard: result.dashboard,
            insights: result.insights,
            executionTime: result.executionTime,
          });
        } catch (error) {
          updateMessage(assistantMessageId, {
            content: 'Sorry, I encountered an error processing your request.',
            status: 'error',
            error: error instanceof Error ? error.message : 'Query failed',
          });
        } finally {
          setStreaming(false);
        }
      }
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Error', 'Failed to send message');
    } finally {
      setLoading(false);
    }
  }, [
    ensureSession,
    addMessage,
    updateMessage,
    setLoading,
    setStreaming,
  ]);
  
  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div
        ref={messagesContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto scrollbar-thin"
      >
        {messages.length === 0 ? (
          <EmptyState />
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
      <AnimatePresence>
        {showScrollButton && (
          <motion.button
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            onClick={() => scrollToBottom()}
            className="absolute bottom-32 right-8 p-2 bg-surface border border-border rounded-full shadow-lg hover:bg-surface-hover transition-colors"
          >
            <ArrowDown className="w-5 h-5 text-foreground" />
          </motion.button>
        )}
      </AnimatePresence>
      
      {/* Input area */}
      <div className="border-t border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <ChatInput
            onSend={handleSend}
            isLoading={isLoading || isStreaming}
          />
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
