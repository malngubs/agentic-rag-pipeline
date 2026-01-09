/**
 * ============================================================================
 * 💬 CHAT PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Main chat page that combines the sidebar and chat interface.
 */

'use client';

import React from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';

export default function ChatPage() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-border bg-background/80 backdrop-blur-sm">
          <div>
            <h1 className="text-lg font-display font-semibold text-foreground">
              AI Assistant
            </h1>
            <p className="text-sm text-foreground-muted">
              Ask questions about your data in natural language
            </p>
          </div>
          
          {/* Quick actions */}
          <div className="flex items-center gap-2">
            <button className="px-3 py-1.5 text-sm text-foreground-secondary hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors">
              Export
            </button>
            <button className="px-3 py-1.5 text-sm text-foreground-secondary hover:text-foreground hover:bg-surface-hover rounded-lg transition-colors">
              Share
            </button>
          </div>
        </header>
        
        {/* Chat interface */}
        <div className="flex-1 min-h-0">
          <ChatInterface />
        </div>
      </main>
    </div>
  );
}
