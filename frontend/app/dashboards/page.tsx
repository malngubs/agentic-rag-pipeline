/**
 * ============================================================================
 * 📊 DASHBOARDS PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Dashboard listing and management page.
 * Users can create, edit, duplicate, and delete dashboards.
 */

'use client';

import React, { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Plus,
  LayoutDashboard,
  MoreVertical,
  Edit,
  Trash2,
  Copy,
  Download,
  Search,
  Grid3X3,
  List,
  Clock,
  X,
  Sparkles,
  BarChart3,
  PieChart,
  TrendingUp,
} from 'lucide-react';
import { Sidebar } from '@/components/layout/Sidebar';
import { useDashboardStore } from '@/lib/stores';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { DashboardData } from '@/types';

// =============================================================================
// CREATE DASHBOARD MODAL
// =============================================================================

interface CreateDashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (title: string, description: string, template: string) => void;
}

const templates = [
  {
    id: 'blank',
    name: 'Blank Dashboard',
    description: 'Start from scratch',
    icon: LayoutDashboard,
  },
  {
    id: 'sales',
    name: 'Sales Overview',
    description: 'Revenue, trends, and KPIs',
    icon: TrendingUp,
  },
  {
    id: 'analytics',
    name: 'Analytics Dashboard',
    description: 'Charts and data visualization',
    icon: BarChart3,
  },
  {
    id: 'financial',
    name: 'Financial Report',
    description: 'Budget, expenses, profit',
    icon: PieChart,
  },
];

const CreateDashboardModal: React.FC<CreateDashboardModalProps> = ({
  isOpen,
  onClose,
  onCreate,
}) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('blank');
  const [step, setStep] = useState<'template' | 'details'>('template');

  const handleCreate = () => {
    if (title.trim()) {
      onCreate(title.trim(), description.trim(), selectedTemplate);
      setTitle('');
      setDescription('');
      setSelectedTemplate('blank');
      setStep('template');
      onClose();
    }
  };

  const handleTemplateSelect = (templateId: string) => {
    setSelectedTemplate(templateId);
    const template = templates.find(t => t.id === templateId);
    if (template && templateId !== 'blank') {
      setTitle(template.name);
      setDescription(template.description);
    }
    setStep('details');
  };

  const handleClose = () => {
    setTitle('');
    setDescription('');
    setSelectedTemplate('blank');
    setStep('template');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-lg bg-surface border border-border rounded-2xl shadow-2xl overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-600/10 flex items-center justify-center">
              <Plus className="w-5 h-5 text-brand-500" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-foreground">
                {step === 'template' ? 'Choose a Template' : 'Dashboard Details'}
              </h2>
              <p className="text-sm text-foreground-muted">
                {step === 'template' ? 'Select how to start' : 'Name your dashboard'}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-surface-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-foreground-muted" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {step === 'template' ? (
            <div className="grid grid-cols-2 gap-3">
              {templates.map((template) => {
                const Icon = template.icon;
                return (
                  <button
                    key={template.id}
                    onClick={() => handleTemplateSelect(template.id)}
                    className={cn(
                      'flex flex-col items-center gap-3 p-4 rounded-xl border transition-all text-left',
                      'hover:bg-surface-hover hover:border-brand-500/50',
                      selectedTemplate === template.id
                        ? 'border-brand-500 bg-brand-600/5'
                        : 'border-border'
                    )}
                  >
                    <div className="w-12 h-12 rounded-xl bg-brand-600/10 flex items-center justify-center">
                      <Icon className="w-6 h-6 text-brand-500" />
                    </div>
                    <div className="text-center">
                      <div className="font-medium text-foreground text-sm">
                        {template.name}
                      </div>
                      <div className="text-xs text-foreground-muted mt-1">
                        {template.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Title input */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Dashboard Name
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="My Dashboard"
                  autoFocus
                  className="w-full px-4 py-3 bg-surface-muted border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 focus:border-brand-600"
                />
              </div>

              {/* Description input */}
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Description (optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="What is this dashboard about?"
                  rows={3}
                  className="w-full px-4 py-3 bg-surface-muted border border-border rounded-lg text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 focus:border-brand-600 resize-none"
                />
              </div>

              {/* Back button */}
              <button
                onClick={() => setStep('template')}
                className="text-sm text-foreground-muted hover:text-foreground transition-colors"
              >
                ← Change template
              </button>
            </div>
          )}
        </div>

        {/* Footer */}
        {step === 'details' && (
          <div className="flex items-center justify-end gap-3 p-6 border-t border-border bg-surface-muted">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-sm font-medium text-foreground-muted hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreate}
              disabled={!title.trim()}
              className="px-6 py-2 bg-brand-600 hover:bg-brand-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium text-sm"
            >
              Create Dashboard
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};

// =============================================================================
// DELETE CONFIRMATION MODAL
// =============================================================================

interface DeleteModalProps {
  isOpen: boolean;
  dashboardTitle: string;
  onClose: () => void;
  onConfirm: () => void;
}

const DeleteModal: React.FC<DeleteModalProps> = ({
  isOpen,
  dashboardTitle,
  onClose,
  onConfirm,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative w-full max-w-md bg-surface border border-border rounded-2xl shadow-2xl p-6"
      >
        <div className="flex items-center gap-4 mb-4">
          <div className="w-12 h-12 rounded-full bg-error/10 flex items-center justify-center">
            <Trash2 className="w-6 h-6 text-error" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-foreground">Delete Dashboard</h3>
            <p className="text-sm text-foreground-muted">This action cannot be undone</p>
          </div>
        </div>
        <p className="text-foreground-muted mb-6">
          Are you sure you want to delete <span className="font-medium text-foreground">"{dashboardTitle}"</span>?
        </p>
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-foreground-muted hover:text-foreground transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="px-6 py-2 bg-error hover:bg-error/90 text-white rounded-lg transition-colors font-medium text-sm"
          >
            Delete
          </button>
        </div>
      </motion.div>
    </div>
  );
};

// =============================================================================
// DASHBOARD CARD COMPONENT
// =============================================================================

interface DashboardCardProps {
  dashboard: DashboardData;
  view: 'grid' | 'list';
  onEdit: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  dashboard,
  view,
  onEdit,
  onDelete,
  onDuplicate,
}) => {
  const [showMenu, setShowMenu] = useState(false);

  if (view === 'list') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-4 p-4 bg-surface border border-border rounded-lg hover:bg-surface-hover transition-colors group"
      >
        {/* Icon */}
        <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center flex-shrink-0">
          <LayoutDashboard className="w-5 h-5 text-brand-500" />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <button onClick={onEdit} className="block text-left">
            <h3 className="font-medium text-foreground truncate hover:text-brand-500 transition-colors">
              {dashboard.title}
            </h3>
            {dashboard.description && (
              <p className="text-sm text-foreground-muted truncate">
                {dashboard.description}
              </p>
            )}
          </button>
        </div>

        {/* Meta */}
        <div className="flex items-center gap-6 text-sm text-foreground-muted">
          <div className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            <span>{formatRelativeTime(dashboard.updatedAt)}</span>
          </div>
          <div>{dashboard.widgets.length} widgets</div>
        </div>

        {/* Actions */}
        <div className="relative">
          <button
            onClick={() => setShowMenu(!showMenu)}
            className="p-2 opacity-0 group-hover:opacity-100 hover:bg-surface-active rounded-lg transition-all"
          >
            <MoreVertical className="w-4 h-4 text-foreground-muted" />
          </button>

          <AnimatePresence>
            {showMenu && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="absolute right-0 top-full mt-1 w-40 bg-surface border border-border rounded-lg shadow-lg z-10"
                onMouseLeave={() => setShowMenu(false)}
              >
                <button
                  onClick={() => { onEdit(); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={() => { onDuplicate(); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                >
                  <Copy className="w-4 h-4" />
                  Duplicate
                </button>
                <button
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                >
                  <Download className="w-4 h-4" />
                  Export
                </button>
                <div className="h-px bg-border my-1" />
                <button
                  onClick={() => { onDelete(); setShowMenu(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-error hover:bg-error/10 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    );
  }

  // Grid view
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface border border-border rounded-xl overflow-hidden hover:shadow-card-hover transition-all group"
    >
      {/* Preview area */}
      <button onClick={onEdit} className="w-full text-left">
        <div className="aspect-video bg-surface-muted flex items-center justify-center border-b border-border">
          <div className="grid grid-cols-2 gap-2 p-4 opacity-50">
            <div className="h-12 bg-surface rounded" />
            <div className="h-12 bg-surface rounded" />
            <div className="h-12 bg-surface rounded col-span-2" />
          </div>
        </div>
      </button>

      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <button onClick={onEdit} className="text-left">
              <h3 className="font-medium text-foreground truncate hover:text-brand-500 transition-colors">
                {dashboard.title}
              </h3>
            </button>
            {dashboard.description && (
              <p className="text-sm text-foreground-muted truncate mt-1">
                {dashboard.description}
              </p>
            )}
          </div>

          {/* Menu */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-1.5 opacity-0 group-hover:opacity-100 hover:bg-surface-hover rounded transition-all"
            >
              <MoreVertical className="w-4 h-4 text-foreground-muted" />
            </button>

            <AnimatePresence>
              {showMenu && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.95 }}
                  className="absolute right-0 top-full mt-1 w-40 bg-surface border border-border rounded-lg shadow-lg z-10"
                  onMouseLeave={() => setShowMenu(false)}
                >
                  <button
                    onClick={() => { onEdit(); setShowMenu(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                  >
                    <Edit className="w-4 h-4" />
                    Edit
                  </button>
                  <button
                    onClick={() => { onDuplicate(); setShowMenu(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                  >
                    <Copy className="w-4 h-4" />
                    Duplicate
                  </button>
                  <button
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Export
                  </button>
                  <div className="h-px bg-border my-1" />
                  <button
                    onClick={() => { onDelete(); setShowMenu(false); }}
                    className="w-full flex items-center gap-2 px-3 py-2 text-sm text-error hover:bg-error/10 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Meta */}
        <div className="flex items-center gap-4 mt-3 text-xs text-foreground-muted">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{formatRelativeTime(dashboard.updatedAt)}</span>
          </div>
          <div>{dashboard.widgets.length} widgets</div>
        </div>
      </div>
    </motion.div>
  );
};

// =============================================================================
// DASHBOARDS PAGE
// =============================================================================

export default function DashboardsPage() {
  const router = useRouter();
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<DashboardData | null>(null);

  const { dashboards, addDashboard, removeDashboard, setCurrentDashboard } = useDashboardStore();

  // Filter dashboards by search
  const filteredDashboards = dashboards.filter((d) =>
    d.title.toLowerCase().includes(search.toLowerCase())
  );

  // Handle create dashboard
  const handleCreate = useCallback((title: string, description: string, template: string) => {
    const newDashboard: DashboardData = {
      id: `dashboard-${Date.now()}`,
      title,
      description,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      widgets: [],
    };

    addDashboard(newDashboard);
    setCurrentDashboard(newDashboard);

    // Navigate to chat to start building the dashboard with AI
    router.push(`/chat?dashboard=${newDashboard.id}`);
  }, [addDashboard, setCurrentDashboard, router]);

  // Handle edit dashboard
  const handleEdit = useCallback((dashboard: DashboardData) => {
    setCurrentDashboard(dashboard);
    router.push(`/chat?dashboard=${dashboard.id}`);
  }, [setCurrentDashboard, router]);

  // Handle duplicate dashboard
  const handleDuplicate = useCallback((dashboard: DashboardData) => {
    const duplicate: DashboardData = {
      ...dashboard,
      id: `dashboard-${Date.now()}`,
      title: `${dashboard.title} (Copy)`,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    addDashboard(duplicate);
  }, [addDashboard]);

  // Handle delete dashboard
  const handleDelete = useCallback(() => {
    if (deleteTarget) {
      removeDashboard(deleteTarget.id);
      setDeleteTarget(null);
    }
  }, [deleteTarget, removeDashboard]);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-background/80 backdrop-blur-sm">
          <div>
            <h1 className="text-lg font-display font-semibold text-foreground">
              Dashboards
            </h1>
            <p className="text-sm text-foreground-muted">
              Create and manage your BI dashboards
            </p>
          </div>

          {/* Create button */}
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors font-medium text-sm"
          >
            <Plus className="w-4 h-4" />
            New Dashboard
          </button>
        </header>

        {/* Toolbar - only show when there are dashboards */}
        {dashboards.length > 0 && (
          <div className="flex items-center justify-between px-6 py-3 border-b border-border">
            {/* Search */}
            <div className="relative w-80">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search dashboards..."
                className="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 focus:border-brand-600"
              />
            </div>

            {/* View toggle */}
            <div className="flex items-center gap-1 p-1 bg-surface border border-border rounded-lg">
              <button
                onClick={() => setView('grid')}
                className={cn(
                  'p-2 rounded transition-colors',
                  view === 'grid'
                    ? 'bg-surface-hover text-foreground'
                    : 'text-foreground-muted hover:text-foreground'
                )}
              >
                <Grid3X3 className="w-4 h-4" />
              </button>
              <button
                onClick={() => setView('list')}
                className={cn(
                  'p-2 rounded transition-colors',
                  view === 'list'
                    ? 'bg-surface-hover text-foreground'
                    : 'text-foreground-muted hover:text-foreground'
                )}
              >
                <List className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          {dashboards.length === 0 ? (
            /* Empty state - no dashboards yet */
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 rounded-2xl glass-brand flex items-center justify-center mb-6 card-glow">
                <LayoutDashboard className="w-10 h-10 text-brand-500" />
              </div>
              <h3 className="text-xl font-semibold text-foreground mb-2">
                Create your first dashboard
              </h3>
              <p className="text-foreground-muted mb-8 max-w-md">
                Build beautiful dashboards with AI assistance. Just describe what you want to see, and we'll help you create it.
              </p>

              {/* Quick start options */}
              <div className="grid grid-cols-2 gap-4 max-w-lg w-full mb-8">
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="flex items-center gap-3 p-4 bg-surface border border-border rounded-xl hover:bg-surface-hover hover:border-brand-500/50 transition-all text-left group"
                >
                  <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Plus className="w-5 h-5 text-brand-500" />
                  </div>
                  <div>
                    <div className="font-medium text-foreground">Start fresh</div>
                    <div className="text-sm text-foreground-muted">Create a blank dashboard</div>
                  </div>
                </button>

                <button
                  onClick={() => router.push('/chat')}
                  className="flex items-center gap-3 p-4 bg-surface border border-border rounded-xl hover:bg-surface-hover hover:border-brand-500/50 transition-all text-left group"
                >
                  <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center group-hover:scale-110 transition-transform">
                    <Sparkles className="w-5 h-5 text-brand-500" />
                  </div>
                  <div>
                    <div className="font-medium text-foreground">Use AI</div>
                    <div className="text-sm text-foreground-muted">Describe what you need</div>
                  </div>
                </button>
              </div>

              <p className="text-sm text-foreground-muted">
                Tip: Upload your data first, then ask the AI to create visualizations
              </p>
            </div>
          ) : filteredDashboards.length === 0 ? (
            /* No search results */
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Search className="w-12 h-12 text-foreground-muted mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                No dashboards found
              </h3>
              <p className="text-foreground-muted">
                Try a different search term
              </p>
            </div>
          ) : (
            /* Dashboard grid/list */
            <div
              className={cn(
                view === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                  : 'space-y-2'
              )}
            >
              {filteredDashboards.map((dashboard) => (
                <DashboardCard
                  key={dashboard.id}
                  dashboard={dashboard}
                  view={view}
                  onEdit={() => handleEdit(dashboard)}
                  onDelete={() => setDeleteTarget(dashboard)}
                  onDuplicate={() => handleDuplicate(dashboard)}
                />
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Modals */}
      <CreateDashboardModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreate}
      />

      <DeleteModal
        isOpen={!!deleteTarget}
        dashboardTitle={deleteTarget?.title || ''}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
      />
    </div>
  );
}
