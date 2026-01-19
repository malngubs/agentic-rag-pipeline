/**
 * ============================================================================
 * 🏠 LANDING PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Marketing/welcome page with navigation to main components.
 * Font: Inter, Segoe UI (matching globals.css)
 */

'use client';

import React from 'react';
import Link from 'next/link';
import { Sparkles, Shield, Zap, BarChart3, Users, Settings } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-border bg-background/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-brand-600 flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="font-display font-bold text-lg text-foreground">Macrocomm</h1>
              <p className="text-xs text-foreground-muted">BI Platform</p>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-4xl w-full text-center">
          {/* Logo */}
          <div className="mb-8 flex justify-center">
            <div className="w-20 h-20 rounded-2xl glossy-button flex items-center justify-center">
              <Sparkles className="w-10 h-10 text-white" />
            </div>
          </div>

          {/* Title */}
          <h1 className="text-5xl font-display font-bold text-foreground mb-4">
            Macrocomm BI Platform
          </h1>
          <p className="text-xl text-foreground-muted mb-8 max-w-2xl mx-auto">
            ChatGPT-like interface for data analytics. Upload your data, ask questions in natural language,
            and get AI-powered insights and visualizations.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-wrap gap-4 justify-center mb-12">
            <Link
              href="/"
              className="glossy-button px-8 py-4 rounded-xl flex items-center gap-3 text-white font-medium text-lg transition-all hover:scale-105"
            >
              <BarChart3 className="w-5 h-5" />
              Open BI Platform
            </Link>

            <Link
              href="/admin"
              className="glass border border-white/10 px-8 py-4 rounded-xl flex items-center gap-3 text-foreground font-medium text-lg transition-all hover:bg-surface-hover"
            >
              <Settings className="w-5 h-5" />
              Admin Portal
            </Link>

            <a
              href="/desktop-app/download"
              className="glass border border-white/10 px-8 py-4 rounded-xl flex items-center gap-3 text-foreground font-medium text-lg transition-all hover:bg-surface-hover"
            >
              <Zap className="w-5 h-5" />
              Download Desktop App
            </a>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-3xl mx-auto">
            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="w-12 h-12 rounded-lg bg-brand-600/20 flex items-center justify-center mb-4 mx-auto">
                <Sparkles className="w-6 h-6 text-brand-500" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">AI-Powered</h3>
              <p className="text-sm text-foreground-muted">
                Natural language queries with GPT-4o-mini
              </p>
            </div>

            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="w-12 h-12 rounded-lg bg-brand-600/20 flex items-center justify-center mb-4 mx-auto">
                <BarChart3 className="w-6 h-6 text-brand-500" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">Smart Visualizations</h3>
              <p className="text-sm text-foreground-muted">
                Automatic chart generation and dashboards
              </p>
            </div>

            <div className="glass border border-white/10 p-6 rounded-xl">
              <div className="w-12 h-12 rounded-lg bg-brand-600/20 flex items-center justify-center mb-4 mx-auto">
                <Shield className="w-6 h-6 text-brand-500" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">Secure & Private</h3>
              <p className="text-sm text-foreground-muted">
                Your data stays in your infrastructure
              </p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-6">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm text-foreground-muted">
          <p>&copy; 2024 Macrocomm. All rights reserved. | Smart Made Simple</p>
        </div>
      </footer>
    </div>
  );
}
