/**
 * ============================================================================
 * 🗄️ ZUSTAND STORES - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * State management using Zustand with persistence and devtools.
 * Includes stores for: Chat, Session, Dashboard, and UI state.
 */

import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type {
  ChatMessage,
  Session,
  DashboardData,
  DashboardWidget,
  UploadedFile,
  Toast,
  Theme,
  QueryResult,
} from '@/types';

// =============================================================================
// CHAT STORE
// =============================================================================

interface ChatState {
  // State
  messages: ChatMessage[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  
  // Actions
  addMessage: (message: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  removeMessage: (id: string) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setStreaming: (streaming: boolean) => void;
  setError: (error: string | null) => void;
  
  // Streaming helpers
  appendToLastMessage: (content: string) => void;
  finalizeLastMessage: (result: QueryResult) => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    immer((set, get) => ({
      // Initial state
      messages: [],
      isLoading: false,
      isStreaming: false,
      error: null,
      
      // Actions
      addMessage: (message) =>
        set((state) => {
          state.messages.push(message);
        }),
      
      updateMessage: (id, updates) =>
        set((state) => {
          const index = state.messages.findIndex((m) => m.id === id);
          if (index !== -1) {
            state.messages[index] = { ...state.messages[index], ...updates };
          }
        }),
      
      removeMessage: (id) =>
        set((state) => {
          state.messages = state.messages.filter((m) => m.id !== id);
        }),
      
      clearMessages: () =>
        set((state) => {
          state.messages = [];
        }),
      
      setLoading: (loading) =>
        set((state) => {
          state.isLoading = loading;
        }),
      
      setStreaming: (streaming) =>
        set((state) => {
          state.isStreaming = streaming;
        }),
      
      setError: (error) =>
        set((state) => {
          state.error = error;
        }),
      
      // Streaming helpers
      appendToLastMessage: (content) =>
        set((state) => {
          const lastIndex = state.messages.length - 1;
          if (lastIndex >= 0 && state.messages[lastIndex].role === 'assistant') {
            state.messages[lastIndex].content += content;
          }
        }),
      
      finalizeLastMessage: (result) =>
        set((state) => {
          const lastIndex = state.messages.length - 1;
          if (lastIndex >= 0 && state.messages[lastIndex].role === 'assistant') {
            state.messages[lastIndex].status = 'complete';
            state.messages[lastIndex].charts = result.charts;
            state.messages[lastIndex].dashboard = result.dashboard;
            state.messages[lastIndex].insights = result.insights;
            state.messages[lastIndex].executionTime = result.executionTime;
          }
          state.isStreaming = false;
        }),
    })),
    { name: 'chat-store' }
  )
);

// =============================================================================
// SESSION STORE
// =============================================================================

interface SessionState {
  // State
  currentSession: Session | null;
  sessions: Session[];
  uploadedFiles: UploadedFile[];
  isCreating: boolean;
  isUploading: boolean;
  uploadProgress: number;
  
  // Actions
  setCurrentSession: (session: Session | null) => void;
  addSession: (session: Session) => void;
  removeSession: (id: string) => void;
  updateSession: (id: string, updates: Partial<Session>) => void;
  
  // File upload
  addUploadedFile: (file: UploadedFile) => void;
  updateUploadedFile: (id: string, updates: Partial<UploadedFile>) => void;
  removeUploadedFile: (id: string) => void;
  clearUploadedFiles: () => void;
  setUploading: (uploading: boolean) => void;
  setUploadProgress: (progress: number) => void;
  
  // Session creation
  setCreating: (creating: boolean) => void;
}

export const useSessionStore = create<SessionState>()(
  devtools(
    persist(
      immer((set) => ({
        // Initial state
        currentSession: null,
        sessions: [],
        uploadedFiles: [],
        isCreating: false,
        isUploading: false,
        uploadProgress: 0,
        
        // Actions
        setCurrentSession: (session) =>
          set((state) => {
            state.currentSession = session;
          }),
        
        addSession: (session) =>
          set((state) => {
            state.sessions.unshift(session);
          }),
        
        removeSession: (id) =>
          set((state) => {
            state.sessions = state.sessions.filter((s) => s.id !== id);
            if (state.currentSession?.id === id) {
              state.currentSession = null;
            }
          }),
        
        updateSession: (id, updates) =>
          set((state) => {
            const index = state.sessions.findIndex((s) => s.id === id);
            if (index !== -1) {
              state.sessions[index] = { ...state.sessions[index], ...updates };
            }
            if (state.currentSession?.id === id) {
              state.currentSession = { ...state.currentSession, ...updates };
            }
          }),
        
        // File upload actions
        addUploadedFile: (file) =>
          set((state) => {
            state.uploadedFiles.push(file);
          }),
        
        updateUploadedFile: (id, updates) =>
          set((state) => {
            const index = state.uploadedFiles.findIndex((f) => f.id === id);
            if (index !== -1) {
              state.uploadedFiles[index] = { ...state.uploadedFiles[index], ...updates };
            }
          }),
        
        removeUploadedFile: (id) =>
          set((state) => {
            state.uploadedFiles = state.uploadedFiles.filter((f) => f.id !== id);
          }),
        
        clearUploadedFiles: () =>
          set((state) => {
            state.uploadedFiles = [];
          }),
        
        setUploading: (uploading) =>
          set((state) => {
            state.isUploading = uploading;
          }),
        
        setUploadProgress: (progress) =>
          set((state) => {
            state.uploadProgress = progress;
          }),
        
        setCreating: (creating) =>
          set((state) => {
            state.isCreating = creating;
          }),
      })),
      {
        name: 'session-storage',
        partialize: (state) => ({
          sessions: state.sessions.slice(0, 10), // Keep last 10 sessions
        }),
      }
    ),
    { name: 'session-store' }
  )
);

// =============================================================================
// DASHBOARD STORE
// =============================================================================

interface DashboardState {
  // State
  currentDashboard: DashboardData | null;
  dashboards: DashboardData[];
  selectedWidget: string | null;
  isEditing: boolean;
  isSaving: boolean;
  hasUnsavedChanges: boolean;
  
  // Actions
  setCurrentDashboard: (dashboard: DashboardData | null) => void;
  addDashboard: (dashboard: DashboardData) => void;
  updateDashboard: (id: string, updates: Partial<DashboardData>) => void;
  removeDashboard: (id: string) => void;
  
  // Widget actions
  addWidget: (widget: DashboardWidget) => void;
  updateWidget: (widgetId: string, updates: Partial<DashboardWidget>) => void;
  removeWidget: (widgetId: string) => void;
  updateWidgetLayout: (widgetId: string, layout: DashboardWidget['layout']) => void;
  selectWidget: (widgetId: string | null) => void;
  
  // Editor state
  setEditing: (editing: boolean) => void;
  setSaving: (saving: boolean) => void;
  setHasUnsavedChanges: (hasChanges: boolean) => void;
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    persist(
      immer((set) => ({
      // Initial state
      currentDashboard: null,
      dashboards: [],
      selectedWidget: null,
      isEditing: false,
      isSaving: false,
      hasUnsavedChanges: false,
      
      // Actions
      setCurrentDashboard: (dashboard) =>
        set((state) => {
          state.currentDashboard = dashboard;
          state.selectedWidget = null;
          state.hasUnsavedChanges = false;
        }),
      
      addDashboard: (dashboard) =>
        set((state) => {
          state.dashboards.unshift(dashboard);
        }),
      
      updateDashboard: (id, updates) =>
        set((state) => {
          const index = state.dashboards.findIndex((d) => d.id === id);
          if (index !== -1) {
            state.dashboards[index] = { ...state.dashboards[index], ...updates };
          }
          if (state.currentDashboard?.id === id) {
            state.currentDashboard = { ...state.currentDashboard, ...updates };
          }
        }),
      
      removeDashboard: (id) =>
        set((state) => {
          state.dashboards = state.dashboards.filter((d) => d.id !== id);
          if (state.currentDashboard?.id === id) {
            state.currentDashboard = null;
          }
        }),
      
      // Widget actions
      addWidget: (widget) =>
        set((state) => {
          if (state.currentDashboard) {
            state.currentDashboard.widgets.push(widget);
            state.hasUnsavedChanges = true;
          }
        }),
      
      updateWidget: (widgetId, updates) =>
        set((state) => {
          if (state.currentDashboard) {
            const index = state.currentDashboard.widgets.findIndex(
              (w) => w.id === widgetId
            );
            if (index !== -1) {
              state.currentDashboard.widgets[index] = {
                ...state.currentDashboard.widgets[index],
                ...updates,
              };
              state.hasUnsavedChanges = true;
            }
          }
        }),
      
      removeWidget: (widgetId) =>
        set((state) => {
          if (state.currentDashboard) {
            state.currentDashboard.widgets = state.currentDashboard.widgets.filter(
              (w) => w.id !== widgetId
            );
            if (state.selectedWidget === widgetId) {
              state.selectedWidget = null;
            }
            state.hasUnsavedChanges = true;
          }
        }),
      
      updateWidgetLayout: (widgetId, layout) =>
        set((state) => {
          if (state.currentDashboard) {
            const index = state.currentDashboard.widgets.findIndex(
              (w) => w.id === widgetId
            );
            if (index !== -1) {
              state.currentDashboard.widgets[index].layout = layout;
              state.hasUnsavedChanges = true;
            }
          }
        }),
      
      selectWidget: (widgetId) =>
        set((state) => {
          state.selectedWidget = widgetId;
        }),
      
      // Editor state
      setEditing: (editing) =>
        set((state) => {
          state.isEditing = editing;
        }),
      
      setSaving: (saving) =>
        set((state) => {
          state.isSaving = saving;
        }),
      
      setHasUnsavedChanges: (hasChanges) =>
        set((state) => {
          state.hasUnsavedChanges = hasChanges;
        }),
    })),
      {
        name: 'dashboard-storage',
        partialize: (state) => ({
          dashboards: state.dashboards,
          currentDashboard: state.currentDashboard,
        }),
      }
    ),
    { name: 'dashboard-store' }
  )
);

// =============================================================================
// UI STORE
// =============================================================================

interface UIState {
  // Sidebar
  sidebarOpen: boolean;
  sidebarCollapsed: boolean;
  activeSection: 'chat' | 'dashboards' | 'documents' | 'settings';
  
  // Theme
  theme: Theme;
  
  // Modals
  activeModal: 'upload' | 'export' | 'settings' | 'confirm' | 'widget-picker' | null;
  modalData: any;
  
  // Toasts
  toasts: Toast[];
  
  // Loading states
  globalLoading: boolean;
  loadingMessage: string;
  
  // Command palette
  commandPaletteOpen: boolean;
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
  setActiveSection: (section: UIState['activeSection']) => void;
  
  setTheme: (theme: Theme) => void;
  
  openModal: (modal: UIState['activeModal'], data?: any) => void;
  closeModal: () => void;
  
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  
  setGlobalLoading: (loading: boolean, message?: string) => void;
  
  toggleCommandPalette: () => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      immer((set) => ({
        // Initial state
        sidebarOpen: true,
        sidebarCollapsed: false,
        activeSection: 'chat',
        theme: 'dark',
        activeModal: null,
        modalData: null,
        toasts: [],
        globalLoading: false,
        loadingMessage: '',
        commandPaletteOpen: false,
        
        // Sidebar actions
        toggleSidebar: () =>
          set((state) => {
            state.sidebarOpen = !state.sidebarOpen;
          }),
        
        setSidebarOpen: (open) =>
          set((state) => {
            state.sidebarOpen = open;
          }),
        
        setSidebarCollapsed: (collapsed) =>
          set((state) => {
            state.sidebarCollapsed = collapsed;
          }),
        
        setActiveSection: (section) =>
          set((state) => {
            state.activeSection = section;
          }),
        
        // Theme
        setTheme: (theme) =>
          set((state) => {
            state.theme = theme;
          }),
        
        // Modal actions
        openModal: (modal, data) =>
          set((state) => {
            state.activeModal = modal;
            state.modalData = data;
          }),
        
        closeModal: () =>
          set((state) => {
            state.activeModal = null;
            state.modalData = null;
          }),
        
        // Toast actions
        addToast: (toast) =>
          set((state) => {
            const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
            state.toasts.push({ ...toast, id });
            
            // Auto-remove after duration (default 5 seconds)
            const duration = toast.duration || 5000;
            setTimeout(() => {
              set((s) => {
                s.toasts = s.toasts.filter((t) => t.id !== id);
              });
            }, duration);
          }),
        
        removeToast: (id) =>
          set((state) => {
            state.toasts = state.toasts.filter((t) => t.id !== id);
          }),
        
        // Loading
        setGlobalLoading: (loading, message = '') =>
          set((state) => {
            state.globalLoading = loading;
            state.loadingMessage = message;
          }),
        
        // Command palette
        toggleCommandPalette: () =>
          set((state) => {
            state.commandPaletteOpen = !state.commandPaletteOpen;
          }),
        
        setCommandPaletteOpen: (open) =>
          set((state) => {
            state.commandPaletteOpen = open;
          }),
      })),
      {
        name: 'ui-storage',
        partialize: (state) => ({
          theme: state.theme,
          sidebarCollapsed: state.sidebarCollapsed,
        }),
      }
    ),
    { name: 'ui-store' }
  )
);

// =============================================================================
// HELPER HOOKS
// =============================================================================

// Get all stores in one hook (for components that need multiple stores)
export const useStores = () => ({
  chat: useChatStore(),
  session: useSessionStore(),
  dashboard: useDashboardStore(),
  ui: useUIStore(),
});

// Toast helper
export const toast = {
  success: (title: string, message?: string) =>
    useUIStore.getState().addToast({ type: 'success', title, message }),
  error: (title: string, message?: string) =>
    useUIStore.getState().addToast({ type: 'error', title, message }),
  warning: (title: string, message?: string) =>
    useUIStore.getState().addToast({ type: 'warning', title, message }),
  info: (title: string, message?: string) =>
    useUIStore.getState().addToast({ type: 'info', title, message }),
};
