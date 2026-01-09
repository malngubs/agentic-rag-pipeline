/**
 * ============================================================================
 * 🏠 ROOT LAYOUT - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Root layout with fonts and global providers.
 * Uses Google Fonts instead of local font files.
 */

import type { Metadata, Viewport } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

// =============================================================================
// FONTS - Using Google Fonts (no local files needed)
// =============================================================================

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
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
  keywords: ['BI', 'Business Intelligence', 'AI', 'Analytics', 'Dashboard', 'Macrocomm'],
  authors: [{ name: 'Macrocomm' }],
  creator: 'Macrocomm',
  publisher: 'Macrocomm',
  robots: 'index, follow',
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://bi.macrocomm.ai',
    siteName: 'Macrocomm BI Platform',
    title: 'Macrocomm BI Platform',
    description: 'AI-powered Business Intelligence Platform',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Macrocomm BI Platform',
    description: 'AI-powered Business Intelligence Platform',
  },
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
      <body className="min-h-screen bg-background font-sans antialiased">
        {/* Background effects */}
        <div className="fixed inset-0 -z-10 overflow-hidden">
          {/* Gradient background */}
          <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-surface" />
          
          {/* Subtle grid pattern */}
          <div 
            className="absolute inset-0 opacity-[0.02]"
            style={{
              backgroundImage: `linear-gradient(rgba(255,110,0,0.1) 1px, transparent 1px),
                               linear-gradient(90deg, rgba(255,110,0,0.1) 1px, transparent 1px)`,
              backgroundSize: '64px 64px',
            }}
          />
          
          {/* Gradient orbs */}
          <div className="absolute -top-40 -right-40 h-80 w-80 rounded-full bg-brand-600/10 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 h-80 w-80 rounded-full bg-brand-600/5 blur-3xl" />
        </div>
        
        {/* Main content */}
        {children}
      </body>
    </html>
  );
}