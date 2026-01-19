/**
 * ============================================================================
 * 💬 CHAT PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Main chat page with AI assistant interface.
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

      {/* Main content - ChatInterface has its own header */}
      <main className="flex-1 flex flex-col min-w-0 relative">
        <ChatInterface />
      </main>
    </div>
  );
}
