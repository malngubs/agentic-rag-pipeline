/**
 * ============================================================================
 * 🛡️ ERROR BOUNDARY - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * React Error Boundary component to gracefully handle errors in the component tree.
 * Prevents the entire app from crashing when a component throws an error.
 *
 * Features:
 * - Catches JavaScript errors in child component tree
 * - Logs error details to console
 * - Displays user-friendly fallback UI
 * - Provides error recovery options
 * - Integrates with error reporting services (optional)
 */

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Component
 * Wraps components to catch and handle errors gracefully
 */
class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error details to console
    console.error('Error Boundary caught an error:', error, errorInfo);

    // Update state with error info
    this.setState({
      error,
      errorInfo,
    });

    // Call optional error callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // Here you can send error to an error reporting service
    // Example: Sentry.captureException(error);
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI provided by parent
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center p-8 bg-background">
          <div className="max-w-md w-full">
            {/* Error Card */}
            <div className="glossy-card rounded-2xl p-8 text-center">
              {/* Error Icon */}
              <div className="w-16 h-16 rounded-full bg-red-600/10 flex items-center justify-center mx-auto mb-6">
                <AlertCircle className="w-8 h-8 text-red-500" />
              </div>

              {/* Title */}
              <h1 className="text-2xl font-bold text-foreground mb-3">
                Something went wrong
              </h1>

              {/* Description */}
              <p className="text-foreground-muted mb-6">
                We encountered an unexpected error. Don't worry, our team has been notified and we're working on it.
              </p>

              {/* Error Details (Development Only) */}
              {process.env.NODE_ENV === 'development' && this.state.error && (
                <div className="mb-6 p-4 bg-surface-muted rounded-lg text-left">
                  <div className="text-sm font-medium text-foreground mb-2">
                    Error Details:
                  </div>
                  <div className="text-xs text-red-500 font-mono overflow-auto max-h-32">
                    {this.state.error.toString()}
                  </div>
                  {this.state.errorInfo && (
                    <details className="mt-2">
                      <summary className="text-xs text-foreground-muted cursor-pointer">
                        Component Stack
                      </summary>
                      <pre className="text-xs text-foreground-subtle mt-2 overflow-auto max-h-32">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-3">
                <button
                  onClick={this.handleReset}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 glossy-button text-white rounded-lg transition-all"
                >
                  <RefreshCw className="w-4 h-4" />
                  Try Again
                </button>
                <button
                  onClick={this.handleGoHome}
                  className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-surface-hover text-foreground rounded-lg hover:bg-surface-active transition-all"
                >
                  <Home className="w-4 h-4" />
                  Go Home
                </button>
              </div>
            </div>

            {/* Help Text */}
            <p className="text-center text-sm text-foreground-subtle mt-4">
              If this problem persists, please{' '}
              <a
                href="mailto:support@macrocomm.ai"
                className="text-brand-500 hover:text-brand-400 underline"
              >
                contact support
              </a>
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

/**
 * Usage Examples:
 *
 * 1. Wrap entire app:
 *    <ErrorBoundary>
 *      <App />
 *    </ErrorBoundary>
 *
 * 2. Wrap specific components:
 *    <ErrorBoundary onError={(error, info) => logErrorToService(error, info)}>
 *      <ChatInterface />
 *    </ErrorBoundary>
 *
 * 3. Custom fallback UI:
 *    <ErrorBoundary fallback={<CustomErrorPage />}>
 *      <Dashboard />
 *    </ErrorBoundary>
 */
