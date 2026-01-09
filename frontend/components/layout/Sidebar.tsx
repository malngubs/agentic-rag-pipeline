/**
 * ============================================================================
 * 📱 SIDEBAR - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Main navigation sidebar with collapsible design and smooth animations.
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  LayoutDashboard,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  LogOut,
  HelpCircle,
  Sparkles,
  Plus,
  Search,
} from 'lucide-react';
import { useUIStore, useSessionStore } from '@/lib/stores';

// =============================================================================
// NAVIGATION ITEMS
// =============================================================================

interface NavItem {
  id: string;
  label: string;
  icon: React.ElementType;
  href: string;
  badge?: number;
}

const mainNavItems: NavItem[] = [
  {
    id: 'chat',
    label: 'Chat',
    icon: MessageSquare,
    href: '/chat',
  },
  {
    id: 'dashboards',
    label: 'Dashboards',
    icon: LayoutDashboard,
    href: '/dashboards',
  },
  {
    id: 'documents',
    label: 'Documents',
    icon: FileText,
    href: '/documents',
  },
];

const bottomNavItems: NavItem[] = [
  {
    id: 'help',
    label: 'Help & Support',
    icon: HelpCircle,
    href: '/help',
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    href: '/settings',
  },
];

// =============================================================================
// NAV LINK COMPONENT
// =============================================================================

interface NavLinkProps {
  item: NavItem;
  isCollapsed: boolean;
  isActive: boolean;
}

const NavLink: React.FC<NavLinkProps> = ({ item, isCollapsed, isActive }) => {
  const Icon = item.icon;
  
  return (
    <Link
      href={item.href}
      className={`
        relative flex items-center gap-3 px-3 py-2.5 rounded-lg
        transition-all duration-200 group
        ${isActive
          ? 'bg-brand-600/10 text-brand-500'
          : 'text-foreground-secondary hover:text-foreground hover:bg-surface-hover'
        }
      `}
    >
      {/* Active indicator */}
      {isActive && (
        <motion.div
          layoutId="activeNav"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-brand-500 rounded-r"
        />
      )}
      
      {/* Icon */}
      <Icon className={`w-5 h-5 flex-shrink-0 ${isActive ? 'text-brand-500' : ''}`} />
      
      {/* Label */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            className="text-sm font-medium whitespace-nowrap overflow-hidden"
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>
      
      {/* Badge */}
      {item.badge && !isCollapsed && (
        <span className="ml-auto px-2 py-0.5 text-xs font-medium bg-brand-600/20 text-brand-500 rounded-full">
          {item.badge}
        </span>
      )}
      
      {/* Tooltip for collapsed state */}
      {isCollapsed && (
        <div className="absolute left-full ml-2 px-2 py-1 bg-surface border border-border rounded text-sm text-foreground opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
          {item.label}
        </div>
      )}
    </Link>
  );
};

// =============================================================================
// SIDEBAR COMPONENT
// =============================================================================

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const { sidebarCollapsed, setSidebarCollapsed } = useUIStore();
  const { sessions } = useSessionStore();
  
  // Check which nav item is active
  const isActive = (href: string) => {
    if (href === '/chat') return pathname === '/chat' || pathname === '/';
    return pathname.startsWith(href);
  };
  
  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarCollapsed ? 72 : 260 }}
      transition={{ duration: 0.2, ease: 'easeInOut' }}
      className="flex flex-col h-full bg-surface-muted border-r border-border"
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border">
        <Link href="/" className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center flex-shrink-0">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          
          {/* Title */}
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="overflow-hidden"
              >
                <div className="font-display font-bold text-foreground whitespace-nowrap">
                  Macrocomm
                </div>
                <div className="text-xs text-foreground-muted whitespace-nowrap">
                  BI Platform
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </Link>
        
        {/* Collapse button */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="p-1.5 hover:bg-surface-hover rounded-lg transition-colors"
        >
          {sidebarCollapsed ? (
            <ChevronRight className="w-4 h-4 text-foreground-muted" />
          ) : (
            <ChevronLeft className="w-4 h-4 text-foreground-muted" />
          )}
        </button>
      </div>
      
      {/* New chat button */}
      <div className="p-3">
        <Link
          href="/chat"
          className={`
            flex items-center justify-center gap-2 w-full px-4 py-2.5
            bg-brand-600 hover:bg-brand-500 text-white
            rounded-lg transition-colors font-medium text-sm
          `}
        >
          <Plus className="w-4 h-4" />
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.span
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="whitespace-nowrap overflow-hidden"
              >
                New Chat
              </motion.span>
            )}
          </AnimatePresence>
        </Link>
      </div>
      
      {/* Search (when expanded) */}
      <AnimatePresence>
        {!sidebarCollapsed && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="px-3 pb-3 overflow-hidden"
          >
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-foreground-muted" />
              <input
                type="text"
                placeholder="Search..."
                className="w-full pl-9 pr-4 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 focus:border-brand-600"
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      {/* Main navigation */}
      <nav className="flex-1 overflow-y-auto px-3 py-2">
        <div className="space-y-1">
          {mainNavItems.map((item) => (
            <NavLink
              key={item.id}
              item={item}
              isCollapsed={sidebarCollapsed}
              isActive={isActive(item.href)}
            />
          ))}
        </div>
        
        {/* Recent sessions */}
        <AnimatePresence>
          {!sidebarCollapsed && sessions.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-6 overflow-hidden"
            >
              <div className="px-3 mb-2 text-xs font-medium text-foreground-muted uppercase tracking-wider">
                Recent
              </div>
              <div className="space-y-1">
                {sessions.slice(0, 5).map((session) => (
                  <Link
                    key={session.id}
                    href={`/chat?session=${session.id}`}
                    className="flex items-center gap-2 px-3 py-2 text-sm text-foreground-secondary hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors"
                  >
                    <MessageSquare className="w-4 h-4" />
                    <span className="truncate">
                      {session.dataName || 'New conversation'}
                    </span>
                  </Link>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>
      
      {/* Divider */}
      <div className="px-3">
        <div className="h-px bg-border" />
      </div>
      
      {/* Bottom navigation */}
      <nav className="p-3 space-y-1">
        {bottomNavItems.map((item) => (
          <NavLink
            key={item.id}
            item={item}
            isCollapsed={sidebarCollapsed}
            isActive={isActive(item.href)}
          />
        ))}
      </nav>
      
      {/* User profile (placeholder) */}
      <div className="p-3 border-t border-border">
        <div className="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-surface-hover transition-colors cursor-pointer">
          {/* Avatar */}
          <div className="w-8 h-8 rounded-full bg-brand-600/20 flex items-center justify-center flex-shrink-0">
            <span className="text-sm font-medium text-brand-500">A</span>
          </div>
          
          {/* User info */}
          <AnimatePresence>
            {!sidebarCollapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                className="flex-1 min-w-0 overflow-hidden"
              >
                <div className="text-sm font-medium text-foreground truncate">
                  AI King
                </div>
                <div className="text-xs text-foreground-muted truncate">
                  Admin
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          
          {/* Logout button */}
          {!sidebarCollapsed && (
            <button className="p-1.5 hover:bg-surface-active rounded transition-colors">
              <LogOut className="w-4 h-4 text-foreground-muted" />
            </button>
          )}
        </div>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
