/**
 * ============================================================================
 * 🎨 TAILWIND CSS CONFIGURATION - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Custom Tailwind configuration with Macrocomm brand colors,
 * premium dark theme, and custom utilities.
 */

import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    container: {
      center: true,
      padding: '2rem',
      screens: {
        '2xl': '1400px',
      },
    },
    extend: {
      // =========================================
      // COLORS - Dynamic Theme System
      // Uses CSS variables so themes can be changed at runtime
      // =========================================
      colors: {
        // Brand Colors - Using CSS variables for dynamic theming
        brand: {
          50: 'var(--color-brand-50)',
          100: 'var(--color-brand-100)',
          200: 'var(--color-brand-200)',
          300: 'var(--color-brand-300)',
          400: 'var(--color-brand-400)',
          500: 'var(--color-brand-500)',
          600: 'var(--color-brand-600)',  // Primary accent
          700: 'var(--color-brand-700)',
          800: 'var(--color-brand-800)',
          900: 'var(--color-brand-900)',
          950: 'var(--color-brand-950)',
        },
        
        // Background Colors (Premium Dark Theme)
        background: {
          DEFAULT: '#0A0F1C',  // Deep Navy
          secondary: '#1A1F2E', // Slate
          tertiary: '#252B3B',  // Lighter Slate
          elevated: '#2D3548',  // Cards/Modals
        },
        
        // Surface Colors
        surface: {
          DEFAULT: '#1A1F2E',
          hover: '#252B3B',
          active: '#2D3548',
          muted: '#0F1422',
        },
        
        // Text Colors
        foreground: {
          DEFAULT: '#F1F5F9',   // Primary text
          secondary: '#94A3B8', // Secondary text
          muted: '#64748B',     // Muted text
          inverse: '#0A0F1C',   // Text on light bg
        },
        
        // Border Colors
        border: {
          DEFAULT: '#334155',
          light: '#475569',
          lighter: '#64748B',
        },
        
        // Status Colors
        success: {
          DEFAULT: '#10B981',
          light: '#34D399',
          dark: '#059669',
        },
        warning: {
          DEFAULT: '#F59E0B',
          light: '#FBBF24',
          dark: '#D97706',
        },
        error: {
          DEFAULT: '#EF4444',
          light: '#F87171',
          dark: '#DC2626',
        },
        info: {
          DEFAULT: '#3B82F6',
          light: '#60A5FA',
          dark: '#2563EB',
        },
        
        // Chart Colors (First one uses brand, rest are fixed)
        chart: {
          1: 'var(--color-brand-600)', // Dynamic brand color
          2: '#3B82F6', // Blue
          3: '#10B981', // Green
          4: '#F59E0B', // Amber
          5: '#8B5CF6', // Purple
          6: '#EC4899', // Pink
          7: '#06B6D4', // Cyan
          8: '#EF4444', // Red
          9: '#84CC16', // Lime
          10: '#F97316', // Orange variant
        },

        // Shadcn/UI Compatible Colors - Using CSS variables
        card: {
          DEFAULT: '#1A1F2E',
          foreground: '#F1F5F9',
        },
        popover: {
          DEFAULT: '#1A1F2E',
          foreground: '#F1F5F9',
        },
        primary: {
          DEFAULT: 'var(--color-brand-600)',
          foreground: '#FFFFFF',
        },
        secondary: {
          DEFAULT: '#252B3B',
          foreground: '#F1F5F9',
        },
        muted: {
          DEFAULT: '#252B3B',
          foreground: '#94A3B8',
        },
        accent: {
          DEFAULT: 'var(--color-brand-500)',
          foreground: '#FFFFFF',
        },
        destructive: {
          DEFAULT: '#EF4444',
          foreground: '#FFFFFF',
        },
        ring: 'var(--color-brand-600)',
        input: '#334155',
      },
      
      // =========================================
      // FONTS - Premium font stack (consistent across all platforms)
      // Primary: Inter (clean, modern, similar to Segoe UI)
      // Mono: JetBrains Mono (professional code font)
      // =========================================
      fontFamily: {
        sans: [
          'var(--font-sans)',
          'Inter',
          'Segoe UI',
          '-apple-system',
          'BlinkMacSystemFont',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'sans-serif',
        ],
        display: [
          'var(--font-sans)',
          'Inter',
          'Segoe UI',
          '-apple-system',
          'BlinkMacSystemFont',
          'sans-serif',
        ],
        mono: [
          'JetBrains Mono',
          'Consolas',
          'Monaco',
          'Fira Code',
          'monospace',
        ],
      },
      
      // =========================================
      // FONT SIZES
      // =========================================
      fontSize: {
        'xs': ['0.75rem', { lineHeight: '1rem' }],
        'sm': ['0.875rem', { lineHeight: '1.25rem' }],
        'base': ['1rem', { lineHeight: '1.5rem' }],
        'lg': ['1.125rem', { lineHeight: '1.75rem' }],
        'xl': ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
        '5xl': ['3rem', { lineHeight: '1.2' }],
        '6xl': ['3.75rem', { lineHeight: '1.1' }],
        '7xl': ['4.5rem', { lineHeight: '1.1' }],
      },
      
      // =========================================
      // BORDER RADIUS
      // =========================================
      borderRadius: {
        'lg': '0.75rem',
        'md': '0.5rem',
        'sm': '0.25rem',
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      
      // =========================================
      // SHADOWS
      // =========================================
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.4)',
        'DEFAULT': '0 1px 3px 0 rgba(0, 0, 0, 0.4), 0 1px 2px -1px rgba(0, 0, 0, 0.4)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.4), 0 2px 4px -2px rgba(0, 0, 0, 0.4)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.4), 0 4px 6px -4px rgba(0, 0, 0, 0.4)',
        'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.4), 0 8px 10px -6px rgba(0, 0, 0, 0.4)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        'glow': '0 0 40px rgba(255, 110, 0, 0.15)',
        'glow-lg': '0 0 60px rgba(255, 110, 0, 0.2)',
        'glow-brand': '0 0 30px rgba(255, 110, 0, 0.3)',
        'inner': 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.3)',
        'card': '0 4px 20px rgba(0, 0, 0, 0.3)',
        'card-hover': '0 8px 30px rgba(0, 0, 0, 0.4)',
      },
      
      // =========================================
      // ANIMATIONS
      // =========================================
      keyframes: {
        // Accordion animations
        'accordion-down': {
          from: { height: '0' },
          to: { height: 'var(--radix-accordion-content-height)' },
        },
        'accordion-up': {
          from: { height: 'var(--radix-accordion-content-height)' },
          to: { height: '0' },
        },
        
        // Fade animations
        'fade-in': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'fade-out': {
          from: { opacity: '1' },
          to: { opacity: '0' },
        },
        
        // Slide animations
        'slide-in-from-top': {
          from: { transform: 'translateY(-10px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-in-from-bottom': {
          from: { transform: 'translateY(10px)', opacity: '0' },
          to: { transform: 'translateY(0)', opacity: '1' },
        },
        'slide-in-from-left': {
          from: { transform: 'translateX(-10px)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        'slide-in-from-right': {
          from: { transform: 'translateX(10px)', opacity: '0' },
          to: { transform: 'translateX(0)', opacity: '1' },
        },
        
        // Pulse glow
        'pulse-glow': {
          '0%, 100%': {
            boxShadow: '0 0 20px rgba(255, 110, 0, 0.2)',
          },
          '50%': {
            boxShadow: '0 0 40px rgba(255, 110, 0, 0.4)',
          },
        },
        
        // Shimmer (loading effect)
        'shimmer': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(100%)' },
        },
        
        // Spin (loading)
        'spin-slow': {
          from: { transform: 'rotate(0deg)' },
          to: { transform: 'rotate(360deg)' },
        },
        
        // Bounce subtle
        'bounce-subtle': {
          '0%, 100%': {
            transform: 'translateY(0)',
          },
          '50%': {
            transform: 'translateY(-5px)',
          },
        },
        
        // Typing cursor
        'blink': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        
        // Chart reveal
        'chart-reveal': {
          from: { 
            opacity: '0', 
            transform: 'scale(0.95) translateY(10px)' 
          },
          to: { 
            opacity: '1', 
            transform: 'scale(1) translateY(0)' 
          },
        },
        
        // Message slide in
        'message-in': {
          from: { 
            opacity: '0', 
            transform: 'translateY(20px) scale(0.95)' 
          },
          to: { 
            opacity: '1', 
            transform: 'translateY(0) scale(1)' 
          },
        },
        
        // Progress bar
        'progress': {
          from: { transform: 'scaleX(0)' },
          to: { transform: 'scaleX(1)' },
        },
        
        // Gradient shift (for backgrounds)
        'gradient-shift': {
          '0%, 100%': {
            backgroundPosition: '0% 50%',
          },
          '50%': {
            backgroundPosition: '100% 50%',
          },
        },
      },
      
      animation: {
        'accordion-down': 'accordion-down 0.2s ease-out',
        'accordion-up': 'accordion-up 0.2s ease-out',
        'fade-in': 'fade-in 0.3s ease-out',
        'fade-out': 'fade-out 0.3s ease-out',
        'slide-in-from-top': 'slide-in-from-top 0.3s ease-out',
        'slide-in-from-bottom': 'slide-in-from-bottom 0.3s ease-out',
        'slide-in-from-left': 'slide-in-from-left 0.3s ease-out',
        'slide-in-from-right': 'slide-in-from-right 0.3s ease-out',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'shimmer': 'shimmer 2s infinite',
        'spin-slow': 'spin-slow 3s linear infinite',
        'bounce-subtle': 'bounce-subtle 2s ease-in-out infinite',
        'blink': 'blink 1s ease-in-out infinite',
        'chart-reveal': 'chart-reveal 0.5s ease-out',
        'message-in': 'message-in 0.3s ease-out',
        'progress': 'progress 1s ease-out',
        'gradient-shift': 'gradient-shift 5s ease infinite',
      },
      
      // =========================================
      // TRANSITIONS
      // =========================================
      transitionDuration: {
        '400': '400ms',
        '600': '600ms',
        '800': '800ms',
      },
      
      transitionTimingFunction: {
        'bounce-in': 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
        'smooth': 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      
      // =========================================
      // BACKGROUND IMAGES
      // =========================================
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
        'gradient-brand': 'linear-gradient(135deg, #FF6E00 0%, #FF923F 100%)',
        'gradient-dark': 'linear-gradient(180deg, #0A0F1C 0%, #1A1F2E 100%)',
        'gradient-card': 'linear-gradient(180deg, #1A1F2E 0%, #252B3B 100%)',
        'gradient-glow': 'radial-gradient(circle at 50% 0%, rgba(255, 110, 0, 0.1) 0%, transparent 50%)',
        'noise': "url('/noise.png')",
      },
      
      // =========================================
      // SPACING
      // =========================================
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '112': '28rem',
        '128': '32rem',
      },
      
      // =========================================
      // Z-INDEX
      // =========================================
      zIndex: {
        '60': '60',
        '70': '70',
        '80': '80',
        '90': '90',
        '100': '100',
      },
      
      // =========================================
      // BACKDROP BLUR
      // =========================================
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [
    require('tailwindcss-animate'),
    require('@tailwindcss/typography'),
    // Custom plugin for text-shadow
    function({ addUtilities }: { addUtilities: Function }) {
      addUtilities({
        '.text-shadow': {
          textShadow: '0 2px 4px rgba(0, 0, 0, 0.3)',
        },
        '.text-shadow-sm': {
          textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)',
        },
        '.text-shadow-lg': {
          textShadow: '0 4px 8px rgba(0, 0, 0, 0.3)',
        },
        '.text-shadow-brand': {
          textShadow: '0 0 20px rgba(255, 110, 0, 0.5)',
        },
        '.text-glow': {
          textShadow: '0 0 10px currentColor',
        },
      });
    },
  ],
};

export default config;
