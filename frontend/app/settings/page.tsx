/**
 * ============================================================================
 * ⚙️ SETTINGS PAGE - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * Settings page for user preferences, theme customization, and account management.
 */

'use client';

import React, { useState } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { ThemeSelector, useTheme, THEMES } from '@/components/providers/ThemeProvider';
import {
  Palette,
  Bell,
  Shield,
  User,
  Database,
  Download,
  Trash2,
  Check,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';

// =============================================================================
// SETTINGS SECTION COMPONENT
// =============================================================================

interface SettingsSectionProps {
  title: string;
  description: string;
  icon: React.ElementType;
  children: React.ReactNode;
}

const SettingsSection: React.FC<SettingsSectionProps> = ({
  title,
  description,
  icon: Icon,
  children,
}) => {
  return (
    <div className="bg-surface rounded-xl border border-border p-6">
      <div className="flex items-start gap-4 mb-6">
        <div className="w-12 h-12 rounded-lg bg-brand-600/10 flex items-center justify-center flex-shrink-0">
          <Icon className="w-6 h-6 text-brand-500" />
        </div>
        <div className="flex-1">
          <h2 className="text-xl font-semibold text-foreground mb-1">{title}</h2>
          <p className="text-sm text-foreground-muted">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
};

// =============================================================================
// SETTINGS PAGE
// =============================================================================

export default function SettingsPage() {
  const { theme } = useTheme();

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="max-w-4xl mx-auto p-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-foreground mb-2">Settings</h1>
            <p className="text-foreground-secondary">
              Customize your Macrocomm BI experience
            </p>
          </div>

          {/* Settings Sections */}
          <div className="space-y-6">
            {/* Theme Customization */}
            <SettingsSection
              title="Theme & Appearance"
              description="Customize the color theme of your interface"
              icon={Palette}
            >
              <div className="space-y-4">
                {/* Current Theme Display */}
                <div className="p-4 bg-surface-muted rounded-lg">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <div className="text-sm text-foreground-muted mb-1">Current Theme</div>
                      <div className="flex items-center gap-2">
                        <div
                          className="w-8 h-8 rounded-full border-2 border-white shadow-lg"
                          style={{ backgroundColor: theme.colors[600] }}
                        />
                        <span className="text-lg font-medium text-foreground">{theme.name}</span>
                      </div>
                    </div>
                    <div className="px-3 py-1 bg-brand-600/10 text-brand-500 rounded-full text-sm font-medium">
                      Active
                    </div>
                  </div>

                  {/* Color Preview */}
                  <div className="grid grid-cols-10 gap-1">
                    {Object.entries(theme.colors).map(([shade, color]) => (
                      <div
                        key={shade}
                        className="h-8 rounded"
                        style={{ backgroundColor: color }}
                        title={`${theme.name} ${shade}`}
                      />
                    ))}
                  </div>
                </div>

                {/* Theme Selector */}
                <div>
                  <div className="text-sm text-foreground-muted mb-3">Available Themes</div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {THEMES.map((t) => (
                      <ThemeButton key={t.id} theme={t} currentTheme={theme} />
                    ))}
                  </div>
                </div>

                {/* Quick Color Picker */}
                <div className="pt-4 border-t border-border">
                  <div className="text-sm text-foreground-muted mb-3">Quick Pick</div>
                  <ThemeSelector />
                </div>
              </div>
            </SettingsSection>

            {/* Account Settings */}
            <SettingsSection
              title="Account & Profile"
              description="Manage your account information and preferences"
              icon={User}
            >
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Display Name
                  </label>
                  <input
                    type="text"
                    defaultValue="AI King"
                    className="w-full px-4 py-2 bg-surface-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    defaultValue="admin@macrocomm.ai"
                    className="w-full px-4 py-2 bg-surface-muted border border-border rounded-lg text-foreground focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                  />
                </div>
              </div>
            </SettingsSection>

            {/* Notifications */}
            <SettingsSection
              title="Notifications"
              description="Configure how you receive updates and alerts"
              icon={Bell}
            >
              <div className="space-y-3">
                <ToggleSetting
                  label="Email Notifications"
                  description="Receive notifications via email"
                  defaultChecked={true}
                />
                <ToggleSetting
                  label="Dashboard Updates"
                  description="Get notified when dashboards are updated"
                  defaultChecked={true}
                />
                <ToggleSetting
                  label="Query Alerts"
                  description="Alerts when queries complete"
                  defaultChecked={false}
                />
              </div>
            </SettingsSection>

            {/* Data & Privacy */}
            <SettingsSection
              title="Data & Privacy"
              description="Manage your data and privacy settings"
              icon={Shield}
            >
              <div className="space-y-3">
                <ToggleSetting
                  label="Save Query History"
                  description="Store your chat and query history"
                  defaultChecked={true}
                />
                <ToggleSetting
                  label="Analytics Collection"
                  description="Help improve our service by sharing anonymous usage data"
                  defaultChecked={true}
                />
              </div>
            </SettingsSection>

            {/* Data Management */}
            <DataManagementSection />
          </div>

          {/* Save Button */}
          <div className="mt-8 flex justify-end gap-3">
            <button className="px-6 py-2 border border-border text-foreground rounded-lg hover:bg-surface-hover transition-colors">
              Cancel
            </button>
            <button className="px-6 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors flex items-center gap-2">
              <Check className="w-4 h-4" />
              Save Changes
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}

// =============================================================================
// DATA MANAGEMENT SECTION COMPONENT
// =============================================================================

const DataManagementSection: React.FC = () => {
  const [isClearing, setIsClearing] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);
  const [clearError, setClearError] = useState<string | null>(null);

  const handleClearLocalData = async () => {
    setIsClearing(true);
    setClearSuccess(false);
    setClearError(null);

    try {
      // Clear localStorage (where Zustand stores persist)
      const keysToRemove = [
        'session-storage',
        'ui-storage',
        'macrocomm-theme-history',
      ];

      keysToRemove.forEach(key => {
        localStorage.removeItem(key);
      });

      // Clear sessionStorage
      sessionStorage.clear();

      // Keep the theme preference
      // localStorage.getItem('macrocomm-theme') is preserved

      setClearSuccess(true);

      // Auto-hide success message after 3 seconds
      setTimeout(() => setClearSuccess(false), 3000);
    } catch (error) {
      setClearError('Failed to clear local data. Please try again.');
      setTimeout(() => setClearError(null), 5000);
    } finally {
      setIsClearing(false);
    }
  };

  const handleClearAllData = () => {
    if (confirm('Are you sure you want to delete ALL local data? This will clear your session history, preferences, and cached data. This action cannot be undone.')) {
      localStorage.clear();
      sessionStorage.clear();
      alert('All local data has been cleared. The page will now reload.');
      window.location.reload();
    }
  };

  return (
    <SettingsSection
      title="Data Management"
      description="Manage cached data and local storage"
      icon={Database}
    >
      <div className="space-y-4">
        {/* Clear Cache Button */}
        <div className="p-4 bg-surface-muted rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="text-sm font-medium text-foreground">Clear Local Cache</div>
              <div className="text-xs text-foreground-muted mt-1">
                Clears session data and cached information. Useful if you see old data after restarting.
              </div>
            </div>
            <button
              onClick={handleClearLocalData}
              disabled={isClearing}
              className="flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-500 disabled:bg-amber-600/50 text-white rounded-lg transition-colors"
            >
              {isClearing ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4" />
              )}
              {isClearing ? 'Clearing...' : 'Clear Cache'}
            </button>
          </div>

          {/* Success/Error Messages */}
          {clearSuccess && (
            <div className="flex items-center gap-2 mt-2 p-2 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm">
              <Check className="w-4 h-4" />
              Local cache cleared successfully!
            </div>
          )}
          {clearError && (
            <div className="flex items-center gap-2 mt-2 p-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm">
              <AlertCircle className="w-4 h-4" />
              {clearError}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors">
            <Download className="w-4 h-4" />
            Export All Data
          </button>
          <button
            onClick={handleClearAllData}
            className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete All Data
          </button>
        </div>

        {/* Info Note */}
        <div className="text-xs text-foreground-muted p-3 bg-surface-muted rounded-lg border border-border">
          <strong>Note:</strong> Clearing cache will remove stored sessions and UI preferences.
          Your uploaded documents and backend data are not affected. Theme preference is preserved.
        </div>
      </div>
    </SettingsSection>
  );
};

// =============================================================================
// THEME BUTTON COMPONENT
// =============================================================================

interface ThemeButtonProps {
  theme: (typeof THEMES)[0];
  currentTheme: (typeof THEMES)[0];
}

const ThemeButton: React.FC<ThemeButtonProps> = ({ theme, currentTheme }) => {
  const { setTheme } = useTheme();
  const isActive = theme.id === currentTheme.id;

  return (
    <button
      onClick={() => setTheme(theme.id)}
      className={`
        relative p-4 rounded-lg border-2 transition-all
        ${isActive
          ? 'border-brand-500 bg-brand-600/5'
          : 'border-border hover:border-border-light bg-surface'
        }
      `}
    >
      {/* Checkmark for active theme */}
      {isActive && (
        <div className="absolute top-2 right-2 w-5 h-5 bg-brand-500 rounded-full flex items-center justify-center">
          <Check className="w-3 h-3 text-white" />
        </div>
      )}

      {/* Color Circle */}
      <div
        className="w-12 h-12 rounded-full mx-auto mb-2 shadow-lg"
        style={{ backgroundColor: theme.colors[600] }}
      />

      {/* Theme Name */}
      <div className="text-sm font-medium text-foreground text-center">
        {theme.name}
      </div>
    </button>
  );
};

// =============================================================================
// TOGGLE SETTING COMPONENT
// =============================================================================

interface ToggleSettingProps {
  label: string;
  description: string;
  defaultChecked?: boolean;
}

const ToggleSetting: React.FC<ToggleSettingProps> = ({
  label,
  description,
  defaultChecked = false,
}) => {
  const [checked, setChecked] = React.useState(defaultChecked);

  return (
    <div className="flex items-center justify-between p-3 bg-surface-muted rounded-lg">
      <div className="flex-1">
        <div className="text-sm font-medium text-foreground">{label}</div>
        <div className="text-xs text-foreground-muted mt-0.5">{description}</div>
      </div>
      <button
        onClick={() => setChecked(!checked)}
        className={`
          relative w-11 h-6 rounded-full transition-colors
          ${checked ? 'bg-brand-600' : 'bg-surface-active'}
        `}
      >
        <div
          className={`
            absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform
            ${checked ? 'translate-x-5' : 'translate-x-0'}
          `}
        />
      </button>
    </div>
  );
};
