/**
 * ============================================================================
 * 🎨 THEME PROVIDER - WORLD-CLASS THEMING SYSTEM
 * ============================================================================
 *
 * Provides dynamic theme customization across ALL Macrocomm platforms:
 * - BI Dashboard
 * - Admin Portal
 * - Landing Page
 * - Desktop Chatbot
 *
 * Features:
 * - 8 preset color themes with full shade palettes (50-950)
 * - Real-time CSS variable updates
 * - Cross-tab sync via BroadcastChannel
 * - Cross-window sync via storage events
 * - Desktop app sync via custom events + localStorage
 * - Persists user preference
 */

'use client';

import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

// =============================================================================
// THEME DEFINITIONS - Complete color palettes
// =============================================================================

export interface ThemeColors {
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;  // Primary accent
  700: string;
  800: string;
  900: string;
  950: string;
}

export interface Theme {
  id: string;
  name: string;
  colors: ThemeColors;
}

// 8 Preset themes with complete shade palettes
export const THEMES: Theme[] = [
  {
    id: 'orange',
    name: 'Sunset Orange',
    colors: {
      50: '#FFF7ED',
      100: '#FFEDD5',
      200: '#FED7AA',
      300: '#FDBA74',
      400: '#FB923C',
      500: '#FF923F',
      600: '#FF6E00',  // Macrocomm Orange (Default)
      700: '#E65100',
      800: '#C2410C',
      900: '#9A3412',
      950: '#7C2D12',
    },
  },
  {
    id: 'blue',
    name: 'Ocean Blue',
    colors: {
      50: '#EFF6FF',
      100: '#DBEAFE',
      200: '#BFDBFE',
      300: '#93C5FD',
      400: '#60A5FA',
      500: '#3B82F6',
      600: '#2563EB',
      700: '#1D4ED8',
      800: '#1E40AF',
      900: '#1E3A8A',
      950: '#172554',
    },
  },
  {
    id: 'green',
    name: 'Forest Green',
    colors: {
      50: '#ECFDF5',
      100: '#D1FAE5',
      200: '#A7F3D0',
      300: '#6EE7B7',
      400: '#34D399',
      500: '#10B981',
      600: '#059669',
      700: '#047857',
      800: '#065F46',
      900: '#064E3B',
      950: '#022C22',
    },
  },
  {
    id: 'purple',
    name: 'Royal Purple',
    colors: {
      50: '#FAF5FF',
      100: '#F3E8FF',
      200: '#E9D5FF',
      300: '#D8B4FE',
      400: '#C084FC',
      500: '#A855F7',
      600: '#9333EA',
      700: '#7E22CE',
      800: '#6B21A8',
      900: '#581C87',
      950: '#3B0764',
    },
  },
  {
    id: 'pink',
    name: 'Hot Pink',
    colors: {
      50: '#FDF2F8',
      100: '#FCE7F3',
      200: '#FBCFE8',
      300: '#F9A8D4',
      400: '#F472B6',
      500: '#EC4899',
      600: '#DB2777',
      700: '#BE185D',
      800: '#9D174D',
      900: '#831843',
      950: '#500724',
    },
  },
  {
    id: 'cyan',
    name: 'Electric Cyan',
    colors: {
      50: '#ECFEFF',
      100: '#CFFAFE',
      200: '#A5F3FC',
      300: '#67E8F9',
      400: '#22D3EE',
      500: '#06B6D4',
      600: '#0891B2',
      700: '#0E7490',
      800: '#155E75',
      900: '#164E63',
      950: '#083344',
    },
  },
  {
    id: 'red',
    name: 'Ruby Red',
    colors: {
      50: '#FEF2F2',
      100: '#FEE2E2',
      200: '#FECACA',
      300: '#FCA5A5',
      400: '#F87171',
      500: '#EF4444',
      600: '#DC2626',
      700: '#B91C1C',
      800: '#991B1B',
      900: '#7F1D1D',
      950: '#450A0A',
    },
  },
  {
    id: 'amber',
    name: 'Golden Amber',
    colors: {
      50: '#FFFBEB',
      100: '#FEF3C7',
      200: '#FDE68A',
      300: '#FCD34D',
      400: '#FBBF24',
      500: '#F59E0B',
      600: '#D97706',
      700: '#B45309',
      800: '#92400E',
      900: '#78350F',
      950: '#451A03',
    },
  },
];

// =============================================================================
// STORAGE & BROADCAST KEYS
// =============================================================================

const STORAGE_KEY = 'macrocomm-theme';
const BROADCAST_CHANNEL = 'macrocomm-theme-sync';

// =============================================================================
// THEME CONTEXT
// =============================================================================

interface ThemeContextType {
  theme: Theme;
  setTheme: (themeId: string) => void;
  themes: Theme[];
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// =============================================================================
// APPLY THEME TO CSS VARIABLES
// =============================================================================

function applyTheme(theme: Theme) {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;

  // Set all brand color shades as CSS variables
  Object.entries(theme.colors).forEach(([shade, color]) => {
    root.style.setProperty(`--color-brand-${shade}`, color);
  });

  // Set shadcn/ui compatibility variables
  root.style.setProperty('--primary', theme.colors[600]);
  root.style.setProperty('--primary-foreground', '#FFFFFF');
  root.style.setProperty('--accent', theme.colors[500]);
  root.style.setProperty('--accent-foreground', '#FFFFFF');
  root.style.setProperty('--ring', theme.colors[600]);

  // Set RGB values for rgba() usage (extract from hex)
  const hexToRgb = (hex: string) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result
      ? `${parseInt(result[1], 16)}, ${parseInt(result[2], 16)}, ${parseInt(result[3], 16)}`
      : '255, 110, 0';
  };

  root.style.setProperty('--color-brand-rgb', hexToRgb(theme.colors[600]));
  root.style.setProperty('--color-brand-500-rgb', hexToRgb(theme.colors[500]));

  // Add theme ID as data attribute for CSS targeting
  root.setAttribute('data-theme', theme.id);
}

// =============================================================================
// THEME PROVIDER COMPONENT
// =============================================================================

interface ThemeProviderProps {
  children: React.ReactNode;
  defaultTheme?: string;
}

export function ThemeProvider({ children, defaultTheme = 'orange' }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>(() => {
    return THEMES.find(t => t.id === defaultTheme) || THEMES[0];
  });

  const [broadcastChannel, setBroadcastChannel] = useState<BroadcastChannel | null>(null);

  // Initialize BroadcastChannel for cross-tab sync
  useEffect(() => {
    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      const channel = new BroadcastChannel(BROADCAST_CHANNEL);
      setBroadcastChannel(channel);

      // Listen for theme changes from other tabs
      channel.onmessage = (event) => {
        if (event.data?.type === 'THEME_CHANGE' && event.data?.themeId) {
          const newTheme = THEMES.find(t => t.id === event.data.themeId);
          if (newTheme) {
            setThemeState(newTheme);
            applyTheme(newTheme);
          }
        }
      };

      return () => {
        channel.close();
      };
    }
  }, []);

  // Load theme from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const savedThemeId = localStorage.getItem(STORAGE_KEY);
    if (savedThemeId) {
      const savedTheme = THEMES.find(t => t.id === savedThemeId);
      if (savedTheme) {
        setThemeState(savedTheme);
        applyTheme(savedTheme);
      }
    } else {
      applyTheme(theme);
    }

    // Listen for storage changes from other windows
    const handleStorageChange = (event: StorageEvent) => {
      if (event.key === STORAGE_KEY && event.newValue) {
        const newTheme = THEMES.find(t => t.id === event.newValue);
        if (newTheme) {
          setThemeState(newTheme);
          applyTheme(newTheme);
        }
      }
    };

    // Listen for custom theme events (from desktop app or other sources)
    const handleCustomThemeChange = (event: Event) => {
      const customEvent = event as CustomEvent;
      if (customEvent.detail?.themeId) {
        const newTheme = THEMES.find(t => t.id === customEvent.detail.themeId);
        if (newTheme) {
          setThemeState(newTheme);
          applyTheme(newTheme);
        }
      }
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('macrocomm-theme-change', handleCustomThemeChange);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('macrocomm-theme-change', handleCustomThemeChange);
    };
  }, []);

  // Set theme function with cross-platform sync
  const setTheme = useCallback((themeId: string) => {
    const newTheme = THEMES.find(t => t.id === themeId);
    if (!newTheme) return;

    const previousTheme = theme.id;

    // Update local state
    setThemeState(newTheme);
    applyTheme(newTheme);

    // Persist to localStorage (triggers storage event in other windows)
    localStorage.setItem(STORAGE_KEY, themeId);

    // Broadcast to other tabs
    if (broadcastChannel) {
      broadcastChannel.postMessage({ type: 'THEME_CHANGE', themeId });
    }

    // Dispatch custom event for desktop app integration
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('macrocomm-theme-change', {
        detail: { themeId, theme: newTheme, previousTheme }
      }));
    }

    // Track analytics (safe import)
    try {
      import('@/lib/analytics').then(({ trackThemeChange }) => {
        trackThemeChange({
          previousTheme,
          newTheme: themeId,
          timestamp: Date.now(),
        });
      }).catch(() => {});
    } catch (e) {
      // Analytics not available
    }
  }, [broadcastChannel, theme.id]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
}

// =============================================================================
// HOOK TO USE THEME
// =============================================================================

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// =============================================================================
// THEME SELECTOR COMPONENT
// =============================================================================

interface ThemeSelectorProps {
  className?: string;
  showLabels?: boolean;
}

export function ThemeSelector({ className = '', showLabels = false }: ThemeSelectorProps) {
  const { theme, setTheme, themes } = useTheme();

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {themes.map((t) => (
        <button
          key={t.id}
          onClick={() => setTheme(t.id)}
          className={`
            group relative transition-all duration-200
            ${showLabels ? 'flex items-center gap-2 px-3 py-2 rounded-lg' : ''}
            ${theme.id === t.id
              ? showLabels ? 'bg-brand-600/10 ring-2 ring-brand-500' : 'scale-110'
              : showLabels ? 'hover:bg-surface-hover' : 'hover:scale-105'
            }
          `}
          title={t.name}
        >
          <div
            className={`
              rounded-full transition-all duration-200
              ${showLabels ? 'w-6 h-6' : 'w-8 h-8'}
              ${theme.id === t.id
                ? 'ring-2 ring-offset-2 ring-offset-background ring-white'
                : 'ring-2 ring-transparent'
              }
            `}
            style={{ backgroundColor: t.colors[600] }}
          />
          {showLabels && (
            <span className={`text-sm ${theme.id === t.id ? 'text-brand-500 font-medium' : 'text-foreground-muted'}`}>
              {t.name}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// =============================================================================
// UTILITY: Get current theme from localStorage (for non-React usage)
// =============================================================================

export function getCurrentTheme(): Theme {
  if (typeof window === 'undefined') return THEMES[0];

  const savedThemeId = localStorage.getItem(STORAGE_KEY);
  if (savedThemeId) {
    const theme = THEMES.find(t => t.id === savedThemeId);
    if (theme) return theme;
  }
  return THEMES[0];
}

// =============================================================================
// UTILITY: Set theme from outside React (for desktop app)
// =============================================================================

export function setThemeExternal(themeId: string): boolean {
  if (typeof window === 'undefined') return false;

  const theme = THEMES.find(t => t.id === themeId);
  if (!theme) return false;

  // Save to localStorage (triggers sync across all windows/tabs)
  localStorage.setItem(STORAGE_KEY, themeId);

  // Apply theme to CSS
  applyTheme(theme);

  // Dispatch event for React components to pick up
  window.dispatchEvent(new CustomEvent('macrocomm-theme-change', {
    detail: { themeId, theme }
  }));

  return true;
}

export default ThemeProvider;
