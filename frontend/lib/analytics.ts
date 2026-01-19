/**
 * ============================================================================
 * 📊 ANALYTICS SERVICE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Client-side analytics tracking service for user interactions and events.
 * Tracks theme changes, page views, user actions, and performance metrics.
 *
 * Features:
 * - Theme preference tracking
 * - Page view tracking
 * - User interaction events
 * - Error tracking
 * - Performance monitoring
 * - Privacy-first (no PII collection)
 */

interface AnalyticsEvent {
  event: string;
  category: string;
  label?: string;
  value?: number;
  metadata?: Record<string, any>;
}

interface PageViewData {
  path: string;
  title: string;
  referrer?: string;
}

interface ThemeChangeData {
  previousTheme: string;
  newTheme: string;
  timestamp: number;
}

class AnalyticsService {
  private enabled: boolean;
  private sessionId: string;
  private userId?: string;

  constructor() {
    this.enabled = typeof window !== 'undefined' && process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true';
    this.sessionId = this.generateSessionId();
    this.initializeTracking();
  }

  /**
   * Generate unique session ID
   */
  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Initialize tracking services
   */
  private initializeTracking() {
    if (!this.enabled) return;

    // Initialize Google Analytics if GA_ID is provided
    if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_GA_ID) {
      this.initializeGA(process.env.NEXT_PUBLIC_GA_ID);
    }

    // Track initial page view
    this.trackPageView({
      path: window.location.pathname,
      title: document.title,
    });
  }

  /**
   * Initialize Google Analytics
   */
  private initializeGA(gaId: string) {
    // Load Google Analytics script
    const script = document.createElement('script');
    script.async = true;
    script.src = `https://www.googletagmanager.com/gtag/js?id=${gaId}`;
    document.head.appendChild(script);

    // Initialize GA
    (window as any).dataLayer = (window as any).dataLayer || [];
    function gtag(...args: any[]) {
      (window as any).dataLayer.push(arguments);
    }
    gtag('js', new Date());
    gtag('config', gaId, {
      page_path: window.location.pathname,
    });
  }

  /**
   * Set user ID for tracking
   */
  setUserId(userId: string) {
    this.userId = userId;
    this.track({
      event: 'user_identified',
      category: 'user',
      metadata: { userId },
    });
  }

  /**
   * Track generic event
   */
  track(event: AnalyticsEvent) {
    if (!this.enabled) {
      console.debug('[Analytics] Event tracked:', event);
      return;
    }

    // Send to Google Analytics
    if (typeof (window as any).gtag === 'function') {
      (window as any).gtag('event', event.event, {
        event_category: event.category,
        event_label: event.label,
        value: event.value,
        ...event.metadata,
      });
    }

    // Send to custom analytics endpoint (if needed)
    this.sendToBackend(event);

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('[Analytics]', event);
    }
  }

  /**
   * Track page view
   */
  trackPageView(data: PageViewData) {
    this.track({
      event: 'page_view',
      category: 'navigation',
      label: data.path,
      metadata: {
        title: data.title,
        referrer: data.referrer || document.referrer,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Track theme change
   */
  trackThemeChange(data: ThemeChangeData) {
    this.track({
      event: 'theme_changed',
      category: 'customization',
      label: data.newTheme,
      metadata: {
        previousTheme: data.previousTheme,
        newTheme: data.newTheme,
        timestamp: data.timestamp,
        sessionId: this.sessionId,
      },
    });

    // Store theme preference in localStorage for analysis
    try {
      const themeHistory = this.getThemeHistory();
      themeHistory.push({
        theme: data.newTheme,
        timestamp: data.timestamp,
      });

      // Keep only last 50 changes
      if (themeHistory.length > 50) {
        themeHistory.shift();
      }

      localStorage.setItem('macrocomm-theme-history', JSON.stringify(themeHistory));
    } catch (error) {
      console.error('Failed to save theme history:', error);
    }
  }

  /**
   * Get theme change history
   */
  getThemeHistory(): Array<{ theme: string; timestamp: number }> {
    try {
      const history = localStorage.getItem('macrocomm-theme-history');
      return history ? JSON.parse(history) : [];
    } catch {
      return [];
    }
  }

  /**
   * Track user interaction
   */
  trackInteraction(action: string, label?: string, value?: number) {
    this.track({
      event: action,
      category: 'interaction',
      label,
      value,
      metadata: {
        sessionId: this.sessionId,
        timestamp: Date.now(),
      },
    });
  }

  /**
   * Track button click
   */
  trackButtonClick(buttonName: string, location?: string) {
    this.trackInteraction('button_click', buttonName, undefined);
  }

  /**
   * Track search query
   */
  trackSearch(query: string, resultsCount?: number) {
    this.track({
      event: 'search',
      category: 'engagement',
      label: query.substring(0, 100), // Limit query length
      value: resultsCount,
      metadata: {
        queryLength: query.length,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Track file upload
   */
  trackFileUpload(fileName: string, fileSize: number, fileType: string) {
    this.track({
      event: 'file_upload',
      category: 'content',
      label: fileType,
      value: fileSize,
      metadata: {
        fileName: fileName.substring(0, 50),
        fileSize,
        fileType,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Track error
   */
  trackError(error: Error, context?: string) {
    this.track({
      event: 'error',
      category: 'error',
      label: error.message,
      metadata: {
        error: error.toString(),
        stack: error.stack,
        context,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Track performance metric
   */
  trackPerformance(metric: string, value: number, unit: string = 'ms') {
    this.track({
      event: 'performance',
      category: 'performance',
      label: metric,
      value,
      metadata: {
        unit,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Track chat message
   */
  trackChatMessage(messageLength: number, hasAttachment: boolean) {
    this.track({
      event: 'chat_message_sent',
      category: 'engagement',
      value: messageLength,
      metadata: {
        hasAttachment,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Track dashboard view
   */
  trackDashboardView(dashboardId: string, dashboardName?: string) {
    this.track({
      event: 'dashboard_view',
      category: 'content',
      label: dashboardId,
      metadata: {
        dashboardName,
        sessionId: this.sessionId,
      },
    });
  }

  /**
   * Send event to backend analytics endpoint
   */
  private async sendToBackend(event: AnalyticsEvent) {
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) return;

      await fetch(`${apiUrl}/api/analytics/track`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...event,
          sessionId: this.sessionId,
          userId: this.userId,
          timestamp: Date.now(),
          userAgent: navigator.userAgent,
          screen: {
            width: window.screen.width,
            height: window.screen.height,
          },
        }),
      });
    } catch (error) {
      // Silently fail - analytics should not break the app
      console.debug('Failed to send analytics to backend:', error);
    }
  }

  /**
   * Get analytics summary
   */
  getAnalyticsSummary() {
    return {
      sessionId: this.sessionId,
      userId: this.userId,
      enabled: this.enabled,
      themeHistory: this.getThemeHistory(),
    };
  }
}

// Export singleton instance
export const analytics = new AnalyticsService();

// Export convenience functions
export const trackPageView = (data: PageViewData) => analytics.trackPageView(data);
export const trackThemeChange = (data: ThemeChangeData) => analytics.trackThemeChange(data);
export const trackButtonClick = (buttonName: string, location?: string) =>
  analytics.trackButtonClick(buttonName, location);
export const trackSearch = (query: string, resultsCount?: number) =>
  analytics.trackSearch(query, resultsCount);
export const trackFileUpload = (fileName: string, fileSize: number, fileType: string) =>
  analytics.trackFileUpload(fileName, fileSize, fileType);
export const trackError = (error: Error, context?: string) =>
  analytics.trackError(error, context);
export const trackPerformance = (metric: string, value: number, unit?: string) =>
  analytics.trackPerformance(metric, value, unit);
export const trackChatMessage = (messageLength: number, hasAttachment: boolean) =>
  analytics.trackChatMessage(messageLength, hasAttachment);
export const trackDashboardView = (dashboardId: string, dashboardName?: string) =>
  analytics.trackDashboardView(dashboardId, dashboardName);

export default analytics;
