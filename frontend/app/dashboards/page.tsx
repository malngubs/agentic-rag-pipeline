/**
 * ============================================================================
 * 📊 DASHBOARDS PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Dashboard listing and management page.
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
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
  Star,
} from 'lucide-react';
import { Sidebar } from '@/components/layout/Sidebar';
import { useDashboardStore } from '@/lib/stores';
import { cn, formatRelativeTime } from '@/lib/utils';
import type { DashboardData } from '@/types';

// =============================================================================
// MOCK DATA (for demonstration)
// =============================================================================

const mockDashboards: DashboardData[] = [
  {
    id: '1',
    title: 'Sales Overview',
    description: 'Monthly sales metrics and trends',
    createdAt: new Date(Date.now() - 86400000 * 2).toISOString(),
    updatedAt: new Date(Date.now() - 3600000).toISOString(),
    widgets: [],
  },
  {
    id: '2',
    title: 'Marketing Analytics',
    description: 'Campaign performance and ROI',
    createdAt: new Date(Date.now() - 86400000 * 7).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
    widgets: [],
  },
  {
    id: '3',
    title: 'Financial Report',
    description: 'Revenue, expenses, and profit analysis',
    createdAt: new Date(Date.now() - 86400000 * 14).toISOString(),
    updatedAt: new Date(Date.now() - 86400000 * 3).toISOString(),
    widgets: [],
  },
];

// =============================================================================
// DASHBOARD CARD COMPONENT
// =============================================================================

interface DashboardCardProps {
  dashboard: DashboardData;
  view: 'grid' | 'list';
  onEdit?: () => void;
  onDelete?: () => void;
  onDuplicate?: () => void;
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
          <Link href={`/dashboards/${dashboard.id}`} className="block">
            <h3 className="font-medium text-foreground truncate hover:text-brand-500 transition-colors">
              {dashboard.title}
            </h3>
            {dashboard.description && (
              <p className="text-sm text-foreground-muted truncate">
                {dashboard.description}
              </p>
            )}
          </Link>
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
                  onClick={onEdit}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-surface-hover transition-colors"
                >
                  <Edit className="w-4 h-4" />
                  Edit
                </button>
                <button
                  onClick={onDuplicate}
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
                  onClick={onDelete}
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
      <Link href={`/dashboards/${dashboard.id}`}>
        <div className="aspect-video bg-surface-muted flex items-center justify-center border-b border-border">
          <div className="grid grid-cols-2 gap-2 p-4 opacity-50">
            <div className="h-12 bg-surface rounded" />
            <div className="h-12 bg-surface rounded" />
            <div className="h-12 bg-surface rounded col-span-2" />
          </div>
        </div>
      </Link>
      
      {/* Content */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <Link href={`/dashboards/${dashboard.id}`}>
              <h3 className="font-medium text-foreground truncate hover:text-brand-500 transition-colors">
                {dashboard.title}
              </h3>
            </Link>
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
            
            {/* Menu dropdown same as list view */}
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
  const [view, setView] = useState<'grid' | 'list'>('grid');
  const [search, setSearch] = useState('');
  const { dashboards } = useDashboardStore();
  
  // Use mock data if no dashboards
  const displayDashboards = dashboards.length > 0 ? dashboards : mockDashboards;
  
  // Filter dashboards
  const filteredDashboards = displayDashboards.filter((d) =>
    d.title.toLowerCase().includes(search.toLowerCase())
  );
  
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
          <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors font-medium text-sm">
            <Plus className="w-4 h-4" />
            New Dashboard
          </button>
        </header>
        
        {/* Toolbar */}
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
        
        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 scrollbar-thin">
          {filteredDashboards.length === 0 ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-hover border border-border flex items-center justify-center mb-4">
                <LayoutDashboard className="w-8 h-8 text-foreground-muted" />
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">
                No dashboards yet
              </h3>
              <p className="text-foreground-muted mb-6 max-w-md">
                Create your first dashboard to visualize your data with beautiful charts and KPIs.
              </p>
              <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors font-medium text-sm">
                <Plus className="w-4 h-4" />
                Create Dashboard
              </button>
            </div>
          ) : (
            <div
              className={cn(
                view === 'grid'
                  ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'
                  : 'space-y-2'
              )}
            >
              {filteredDashboards.map((dashboard, index) => (
                <DashboardCard
                  key={dashboard.id}
                  dashboard={dashboard}
                  view={view}
                />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
