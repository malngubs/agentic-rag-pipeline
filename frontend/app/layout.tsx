/**
 * ============================================================================
 * 🏠 ROOT LAYOUT - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Root layout with fonts matching the desktop chatbot.
 * Uses system fonts (Segoe UI on Windows) for consistency.
 * 
 * FIXED:
 * - Removed local font files that were causing errors
 * - Using Google Fonts (Inter) as fallback
 * - Font stack matches the desktop app
 */

import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/components/providers/ThemeProvider';
import ErrorBoundary from '@/components/ErrorBoundary';

// =============================================================================
// FONTS - Premium font stack (consistent across all Macrocomm platforms)
// =============================================================================

// Primary font: Inter (clean, modern, similar to Segoe UI)
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
  weight: ['300', '400', '500', '600', '700'],
});

// Code font: JetBrains Mono (professional monospace for code blocks)
const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
  weight: ['400', '500', '600'],
});

// =============================================================================
// METADATA
// =============================================================================

export const metadata: Metadata = {
  title: {
    default: 'Macrocomm BI Platform',
    template: '%s | Macrocomm BI',
  },
  description: 'AI-powered Business Intelligence Platform with natural language queries',
  keywords: ['BI', 'Business Intelligence', 'AI', 'Analytics', 'Dashboard', 'Macrocomm', 'RAG'],
  authors: [{ name: 'Macrocomm' }],
  creator: 'Macrocomm',
  publisher: 'Macrocomm',
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#0A0F1C',
};

// =============================================================================
// ROOT LAYOUT
// =============================================================================

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable}`}
      suppressHydrationWarning
    >
      <head>
        {/* Preconnect to Google Fonts for faster loading */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-background font-sans antialiased">
        <ThemeProvider>
          <ErrorBoundary>
            {/* Background effects for glossy look */}
            <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
              {/* Gradient background */}
              <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-surface" />

              {/* Subtle grid pattern */}
              <div
                className="absolute inset-0 opacity-[0.015]"
                style={{
                  backgroundImage: `linear-gradient(var(--color-brand-600) 1px, transparent 1px),
                                   linear-gradient(90deg, var(--color-brand-600) 1px, transparent 1px)`,
                  backgroundSize: '64px 64px',
                }}
              />

              {/* Gradient orbs for depth */}
              <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-brand-600/5 blur-3xl" />
              <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-brand-600/3 blur-3xl" />
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[600px] w-[600px] rounded-full bg-brand-600/2 blur-3xl" />
            </div>

            {/* Main content */}
            {children}
          </ErrorBoundary>
        </ThemeProvider>
      </body>
    </html>
  );
}