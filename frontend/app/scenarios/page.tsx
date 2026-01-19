/**
 * ============================================================================
 * 🎯 SCENARIO PLANNING - MACROCOMM BI PLATFORM
 * ============================================================================
 *
 * What-If Analysis and Scenario Planning:
 * - Create multiple forecast scenarios
 * - Adjust variables (growth rate, costs, etc.)
 * - Compare scenarios side-by-side
 * - Visualize impact on KPIs
 */

'use client';

import React, { useState, useCallback, useEffect, useRef } from 'react';
import { Sidebar } from '@/components/layout/Sidebar';
import { motion, AnimatePresence } from 'framer-motion';
import { api, AnalysisSession, DataProfile, ForecastResult } from '@/lib/api/client';
import {
  Target,
  TrendingUp,
  TrendingDown,
  Minus,
  Plus,
  Trash2,
  Copy,
  Play,
  Save,
  Upload,
  Loader2,
  AlertCircle,
  X,
  ChevronRight,
  BarChart3,
  LineChart,
  Sliders,
  GitBranch,
  Sparkles,
  ArrowUpRight,
  ArrowDownRight,
  FileSpreadsheet,
  Calculator,
  Percent,
  DollarSign,
  RefreshCw,
  Check,
  Eye,
} from 'lucide-react';

// =============================================================================
// TYPES
// =============================================================================

interface ScenarioVariable {
  id: string;
  name: string;
  baseValue: number;
  adjustedValue: number;
  unit: 'percent' | 'absolute' | 'multiplier';
  type: 'growth' | 'cost' | 'revenue' | 'custom';
}

interface Scenario {
  id: string;
  name: string;
  description: string;
  color: string;
  variables: ScenarioVariable[];
  forecast?: ForecastResult;
  kpis?: {
    totalRevenue: number;
    totalCost: number;
    netProfit: number;
    growthRate: number;
  };
  isBaseline: boolean;
}

interface ScenarioComparison {
  metric: string;
  baseline: number;
  scenarios: { id: string; value: number; change: number }[];
}

// =============================================================================
// CONSTANTS
// =============================================================================

const SCENARIO_COLORS = [
  '#6366F1', // Indigo (baseline)
  '#10B981', // Emerald
  '#F59E0B', // Amber
  '#EF4444', // Red
  '#8B5CF6', // Violet
  '#EC4899', // Pink
];

const DEFAULT_VARIABLES: ScenarioVariable[] = [
  { id: 'growth', name: 'Annual Growth Rate', baseValue: 5, adjustedValue: 5, unit: 'percent', type: 'growth' },
  { id: 'costs', name: 'Operating Costs', baseValue: 0, adjustedValue: 0, unit: 'percent', type: 'cost' },
  { id: 'price', name: 'Price Change', baseValue: 0, adjustedValue: 0, unit: 'percent', type: 'revenue' },
  { id: 'volume', name: 'Volume Change', baseValue: 0, adjustedValue: 0, unit: 'percent', type: 'revenue' },
];

// =============================================================================
// HELPER COMPONENTS
// =============================================================================

const VariableSlider: React.FC<{
  variable: ScenarioVariable;
  onChange: (value: number) => void;
  disabled?: boolean;
}> = ({ variable, onChange, disabled }) => {
  const min = variable.unit === 'multiplier' ? 0 : -50;
  const max = variable.unit === 'multiplier' ? 3 : 50;
  const step = variable.unit === 'multiplier' ? 0.1 : 1;

  const getIcon = () => {
    switch (variable.type) {
      case 'growth': return TrendingUp;
      case 'cost': return DollarSign;
      case 'revenue': return BarChart3;
      default: return Sliders;
    }
  };

  const Icon = getIcon();
  const isPositive = variable.adjustedValue > variable.baseValue;
  const isNegative = variable.adjustedValue < variable.baseValue;
  const changePercent = variable.adjustedValue - variable.baseValue;

  return (
    <div className={`p-4 rounded-xl border transition-colors ${disabled ? 'opacity-50' : ''} ${
      isPositive ? 'border-emerald-500/30 bg-emerald-500/5' :
      isNegative ? 'border-red-500/30 bg-red-500/5' :
      'border-border bg-surface'
    }`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Icon className={`w-4 h-4 ${
            isPositive ? 'text-emerald-500' :
            isNegative ? 'text-red-500' :
            'text-foreground-muted'
          }`} />
          <span className="text-sm font-medium text-foreground">{variable.name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${
            isPositive ? 'text-emerald-500' :
            isNegative ? 'text-red-500' :
            'text-foreground'
          }`}>
            {variable.adjustedValue > 0 ? '+' : ''}{variable.adjustedValue}
            {variable.unit === 'percent' ? '%' : variable.unit === 'multiplier' ? 'x' : ''}
          </span>
          {changePercent !== 0 && (
            <span className={`flex items-center text-xs ${
              isPositive ? 'text-emerald-500' : 'text-red-500'
            }`}>
              {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            </span>
          )}
        </div>
      </div>

      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={variable.adjustedValue}
        onChange={(e) => onChange(parseFloat(e.target.value))}
        disabled={disabled}
        className="w-full h-2 bg-surface-muted rounded-lg appearance-none cursor-pointer accent-brand-600"
      />

      <div className="flex justify-between mt-1 text-xs text-foreground-muted">
        <span>{min}{variable.unit === 'percent' ? '%' : ''}</span>
        <span className="text-foreground-muted">Base: {variable.baseValue}{variable.unit === 'percent' ? '%' : ''}</span>
        <span>{max}{variable.unit === 'percent' ? '%' : ''}</span>
      </div>
    </div>
  );
};

const ScenarioCard: React.FC<{
  scenario: Scenario;
  isActive: boolean;
  onClick: () => void;
  onDelete: () => void;
  onDuplicate: () => void;
}> = ({ scenario, isActive, onClick, onDelete, onDuplicate }) => (
  <div
    onClick={onClick}
    className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
      isActive
        ? 'border-brand-500 bg-brand-600/5 shadow-lg'
        : 'border-border hover:border-brand-500/50'
    }`}
  >
    <div className="flex items-start justify-between mb-2">
      <div className="flex items-center gap-2">
        <div
          className="w-3 h-3 rounded-full"
          style={{ backgroundColor: scenario.color }}
        />
        <span className="font-semibold text-foreground">{scenario.name}</span>
        {scenario.isBaseline && (
          <span className="px-2 py-0.5 text-xs bg-brand-600/10 text-brand-500 rounded">
            Baseline
          </span>
        )}
      </div>
      {!scenario.isBaseline && (
        <div className="flex items-center gap-1">
          <button
            onClick={(e) => { e.stopPropagation(); onDuplicate(); }}
            className="p-1 hover:bg-surface-hover rounded"
            title="Duplicate"
          >
            <Copy className="w-4 h-4 text-foreground-muted" />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            className="p-1 hover:bg-red-500/10 rounded"
            title="Delete"
          >
            <Trash2 className="w-4 h-4 text-red-500" />
          </button>
        </div>
      )}
    </div>

    <p className="text-sm text-foreground-muted mb-3 line-clamp-2">
      {scenario.description || 'No description'}
    </p>

    {scenario.kpis && (
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="p-2 bg-surface-muted rounded">
          <span className="text-foreground-muted">Revenue</span>
          <p className="font-semibold text-foreground">
            ${(scenario.kpis.totalRevenue / 1000000).toFixed(1)}M
          </p>
        </div>
        <div className="p-2 bg-surface-muted rounded">
          <span className="text-foreground-muted">Growth</span>
          <p className={`font-semibold ${scenario.kpis.growthRate >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
            {scenario.kpis.growthRate >= 0 ? '+' : ''}{scenario.kpis.growthRate.toFixed(1)}%
          </p>
        </div>
      </div>
    )}
  </div>
);

const ComparisonChart: React.FC<{
  scenarios: Scenario[];
  metric: 'revenue' | 'profit' | 'growth';
}> = ({ scenarios, metric }) => {
  // Simple bar chart comparison
  const maxValue = Math.max(...scenarios.map(s => {
    if (!s.kpis) return 0;
    switch (metric) {
      case 'revenue': return s.kpis.totalRevenue;
      case 'profit': return s.kpis.netProfit;
      case 'growth': return s.kpis.growthRate;
      default: return 0;
    }
  }));

  const getLabel = () => {
    switch (metric) {
      case 'revenue': return 'Total Revenue';
      case 'profit': return 'Net Profit';
      case 'growth': return 'Growth Rate';
    }
  };

  return (
    <div className="p-4 bg-surface rounded-xl border border-border">
      <h4 className="text-sm font-medium text-foreground mb-4">{getLabel()} Comparison</h4>
      <div className="space-y-3">
        {scenarios.map((scenario) => {
          const value = scenario.kpis ? (
            metric === 'revenue' ? scenario.kpis.totalRevenue :
            metric === 'profit' ? scenario.kpis.netProfit :
            scenario.kpis.growthRate
          ) : 0;
          const percentage = maxValue > 0 ? (Math.abs(value) / Math.abs(maxValue)) * 100 : 0;
          const isNegative = value < 0;

          return (
            <div key={scenario.id}>
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <div
                    className="w-2 h-2 rounded-full"
                    style={{ backgroundColor: scenario.color }}
                  />
                  <span className="text-xs text-foreground-muted">{scenario.name}</span>
                </div>
                <span className={`text-sm font-medium ${isNegative ? 'text-red-500' : 'text-foreground'}`}>
                  {metric === 'growth' ? `${value.toFixed(1)}%` : `$${(value / 1000000).toFixed(2)}M`}
                </span>
              </div>
              <div className="h-2 bg-surface-muted rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor: isNegative ? '#EF4444' : scenario.color,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// =============================================================================
// MAIN SCENARIO PLANNING PAGE
// =============================================================================

export default function ScenariosPage() {
  // Session state
  const [session, setSession] = useState<AnalysisSession | null>(null);
  const [profile, setProfile] = useState<DataProfile | null>(null);

  // Scenarios state
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);

  // UI state
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isCalculating, setIsCalculating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize session and baseline scenario
  useEffect(() => {
    const initSession = async () => {
      try {
        const newSession = await api.session.create();
        setSession(newSession);
      } catch (err) {
        console.error('Failed to create session:', err);
      }
    };
    initSession();
  }, []);

  // Create baseline scenario
  const createBaselineScenario = useCallback(() => {
    const baseline: Scenario = {
      id: 'baseline',
      name: 'Baseline',
      description: 'Current projections based on historical data',
      color: SCENARIO_COLORS[0],
      variables: DEFAULT_VARIABLES.map(v => ({ ...v })),
      isBaseline: true,
      kpis: {
        totalRevenue: 10000000,
        totalCost: 7000000,
        netProfit: 3000000,
        growthRate: 5,
      },
    };
    setScenarios([baseline]);
    setActiveScenarioId('baseline');
  }, []);

  // Handle file upload
  const handleFileUpload = useCallback(async (file: File) => {
    if (!session?.id) return;

    setIsUploading(true);
    setUploadProgress(0);
    setError(null);

    try {
      const uploadResult = await api.session.uploadFile(session.id, file, (progress) => {
        setUploadProgress(progress);
      });

      setSession({
        ...session,
        data_loaded: true,
        file_name: uploadResult.file_name,
        row_count: uploadResult.rows,
        column_count: uploadResult.columns,
      });

      // Load profile
      const profileData = await api.session.getProfile(session.id);
      setProfile(profileData);

      // Create baseline scenario
      createBaselineScenario();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [session, createBaselineScenario]);

  // Get active scenario
  const activeScenario = scenarios.find(s => s.id === activeScenarioId);

  // Add new scenario
  const handleAddScenario = useCallback(() => {
    const newScenario: Scenario = {
      id: `scenario-${Date.now()}`,
      name: `Scenario ${scenarios.length}`,
      description: '',
      color: SCENARIO_COLORS[scenarios.length % SCENARIO_COLORS.length],
      variables: DEFAULT_VARIABLES.map(v => ({ ...v })),
      isBaseline: false,
      kpis: {
        totalRevenue: 10000000,
        totalCost: 7000000,
        netProfit: 3000000,
        growthRate: 5,
      },
    };
    setScenarios(prev => [...prev, newScenario]);
    setActiveScenarioId(newScenario.id);
  }, [scenarios.length]);

  // Delete scenario
  const handleDeleteScenario = useCallback((id: string) => {
    setScenarios(prev => prev.filter(s => s.id !== id));
    if (activeScenarioId === id) {
      setActiveScenarioId('baseline');
    }
  }, [activeScenarioId]);

  // Duplicate scenario
  const handleDuplicateScenario = useCallback((id: string) => {
    const source = scenarios.find(s => s.id === id);
    if (!source) return;

    const newScenario: Scenario = {
      ...source,
      id: `scenario-${Date.now()}`,
      name: `${source.name} (Copy)`,
      isBaseline: false,
      color: SCENARIO_COLORS[scenarios.length % SCENARIO_COLORS.length],
      variables: source.variables.map(v => ({ ...v })),
    };
    setScenarios(prev => [...prev, newScenario]);
    setActiveScenarioId(newScenario.id);
  }, [scenarios]);

  // Update variable in active scenario
  const handleVariableChange = useCallback((variableId: string, value: number) => {
    if (!activeScenarioId) return;

    setScenarios(prev => prev.map(scenario => {
      if (scenario.id !== activeScenarioId) return scenario;

      const updatedVariables = scenario.variables.map(v =>
        v.id === variableId ? { ...v, adjustedValue: value } : v
      );

      // Recalculate KPIs based on variables
      const growthVar = updatedVariables.find(v => v.id === 'growth');
      const costVar = updatedVariables.find(v => v.id === 'costs');
      const priceVar = updatedVariables.find(v => v.id === 'price');
      const volumeVar = updatedVariables.find(v => v.id === 'volume');

      const baseRevenue = 10000000;
      const baseCost = 7000000;

      const growthMultiplier = 1 + ((growthVar?.adjustedValue || 0) / 100);
      const priceMultiplier = 1 + ((priceVar?.adjustedValue || 0) / 100);
      const volumeMultiplier = 1 + ((volumeVar?.adjustedValue || 0) / 100);
      const costMultiplier = 1 + ((costVar?.adjustedValue || 0) / 100);

      const totalRevenue = baseRevenue * growthMultiplier * priceMultiplier * volumeMultiplier;
      const totalCost = baseCost * costMultiplier;
      const netProfit = totalRevenue - totalCost;
      const growthRate = ((totalRevenue - baseRevenue) / baseRevenue) * 100;

      return {
        ...scenario,
        variables: updatedVariables,
        kpis: {
          totalRevenue,
          totalCost,
          netProfit,
          growthRate,
        },
      };
    }));
  }, [activeScenarioId]);

  // Update scenario name/description
  const handleUpdateScenario = useCallback((field: 'name' | 'description', value: string) => {
    if (!activeScenarioId) return;

    setScenarios(prev => prev.map(scenario =>
      scenario.id === activeScenarioId
        ? { ...scenario, [field]: value }
        : scenario
    ));
  }, [activeScenarioId]);

  // Run forecast for all scenarios
  const handleRunForecasts = useCallback(async () => {
    if (!session?.id) return;

    setIsCalculating(true);
    setError(null);

    try {
      // In a real implementation, this would call the backend forecast API
      // for each scenario with their specific variable adjustments
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Simulate forecast results
      setScenarios(prev => prev.map(scenario => ({
        ...scenario,
        forecast: {
          method: 'holt_winters',
          forecast_values: Array.from({ length: 12 }, (_, i) => {
            const base = scenario.kpis?.totalRevenue || 10000000;
            const growth = (scenario.variables.find(v => v.id === 'growth')?.adjustedValue || 5) / 100;
            return base * Math.pow(1 + growth / 12, i + 1) * (0.95 + Math.random() * 0.1);
          }),
          forecast_dates: Array.from({ length: 12 }, (_, i) => {
            const date = new Date();
            date.setMonth(date.getMonth() + i + 1);
            return date.toISOString().slice(0, 7);
          }),
          confidence_lower: [],
          confidence_upper: [],
          confidence_level: 0.95,
          metrics: { mae: 0, rmse: 0, mape: 0 },
          trend_direction: 'increasing',
          seasonality_detected: true,
        },
      })));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Forecast calculation failed');
    } finally {
      setIsCalculating(false);
    }
  }, [session?.id]);

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />

      <main className="flex-1 overflow-hidden bg-background flex flex-col">
        {/* Header */}
        <div className="border-b border-border p-6">
          <div className="flex items-center justify-between max-w-7xl mx-auto">
            <div>
              <h1 className="text-2xl font-bold text-foreground mb-1">Scenario Planning</h1>
              <p className="text-foreground-secondary">
                Create What-If scenarios and compare forecast outcomes
              </p>
            </div>
            {session?.data_loaded && (
              <div className="flex items-center gap-3">
                <button
                  onClick={handleAddScenario}
                  className="flex items-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  New Scenario
                </button>
                <button
                  onClick={handleRunForecasts}
                  disabled={isCalculating}
                  className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {isCalculating ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Play className="w-4 h-4" />
                  )}
                  Calculate Forecasts
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Error banner */}
        {error && (
          <div className="px-6 pt-4 max-w-7xl mx-auto w-full">
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <p className="text-sm text-red-500 flex-1">{error}</p>
              <button onClick={() => setError(null)} className="p-1 hover:bg-red-500/20 rounded">
                <X className="w-4 h-4 text-red-500" />
              </button>
            </div>
          </div>
        )}

        {/* Main content */}
        {!session?.data_loaded ? (
          /* Upload prompt */
          <div className="flex-1 flex items-center justify-center p-8">
            <div className="text-center max-w-md">
              <div className="w-20 h-20 rounded-2xl bg-brand-600/10 flex items-center justify-center mx-auto mb-6">
                <GitBranch className="w-10 h-10 text-brand-500" />
              </div>
              <h2 className="text-2xl font-bold text-foreground mb-2">Scenario Planning</h2>
              <p className="text-foreground-muted mb-8">
                Upload your financial data to create What-If scenarios and compare different forecast outcomes
              </p>

              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls,.json"
                onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                className="hidden"
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={isUploading}
                className="flex items-center justify-center gap-2 w-full px-6 py-4 bg-brand-600 hover:bg-brand-500 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing... {uploadProgress}%
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload Financial Data
                  </>
                )}
              </button>

              <p className="text-xs text-foreground-muted mt-4">
                Or start with sample data for demonstration
              </p>
              <button
                onClick={createBaselineScenario}
                className="mt-2 text-sm text-brand-500 hover:text-brand-400"
              >
                Use Sample Data
              </button>
            </div>
          </div>
        ) : (
          /* Scenario planning interface */
          <div className="flex-1 overflow-hidden flex">
            {/* Left panel - Scenarios list */}
            <div className="w-72 border-r border-border flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border">
                <h3 className="font-semibold text-foreground">Scenarios</h3>
                <p className="text-xs text-foreground-muted mt-1">
                  {scenarios.length} scenario{scenarios.length !== 1 ? 's' : ''} created
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3">
                {scenarios.map((scenario) => (
                  <ScenarioCard
                    key={scenario.id}
                    scenario={scenario}
                    isActive={scenario.id === activeScenarioId}
                    onClick={() => setActiveScenarioId(scenario.id)}
                    onDelete={() => handleDeleteScenario(scenario.id)}
                    onDuplicate={() => handleDuplicateScenario(scenario.id)}
                  />
                ))}
              </div>
            </div>

            {/* Middle panel - Variable adjustments */}
            <div className="w-96 border-r border-border flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-foreground">
                    {activeScenario?.name || 'Select a Scenario'}
                  </h3>
                  {activeScenario && !activeScenario.isBaseline && (
                    <button className="text-xs text-brand-500 hover:text-brand-400">
                      Reset
                    </button>
                  )}
                </div>
              </div>

              {activeScenario ? (
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                  {/* Scenario name & description */}
                  {!activeScenario.isBaseline && (
                    <div className="space-y-3 pb-4 border-b border-border">
                      <input
                        type="text"
                        value={activeScenario.name}
                        onChange={(e) => handleUpdateScenario('name', e.target.value)}
                        className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-foreground font-medium focus:outline-none focus:ring-2 focus:ring-brand-600/50"
                      />
                      <textarea
                        value={activeScenario.description}
                        onChange={(e) => handleUpdateScenario('description', e.target.value)}
                        placeholder="Add a description..."
                        rows={2}
                        className="w-full px-3 py-2 bg-surface border border-border rounded-lg text-sm text-foreground placeholder:text-foreground-muted focus:outline-none focus:ring-2 focus:ring-brand-600/50 resize-none"
                      />
                    </div>
                  )}

                  {/* Variable sliders */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-medium text-foreground-muted">
                      Adjust Variables
                    </h4>
                    {activeScenario.variables.map((variable) => (
                      <VariableSlider
                        key={variable.id}
                        variable={variable}
                        onChange={(value) => handleVariableChange(variable.id, value)}
                        disabled={activeScenario.isBaseline}
                      />
                    ))}
                  </div>

                  {/* Quick actions */}
                  <div className="pt-4 border-t border-border space-y-2">
                    <button
                      onClick={() => handleDuplicateScenario(activeScenario.id)}
                      className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-border rounded-lg hover:bg-surface-hover transition-colors text-sm"
                    >
                      <Copy className="w-4 h-4" />
                      Duplicate Scenario
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center p-4">
                  <p className="text-foreground-muted text-center">
                    Select a scenario to adjust variables
                  </p>
                </div>
              )}
            </div>

            {/* Right panel - Comparison & Results */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-4 border-b border-border">
                <h3 className="font-semibold text-foreground">Scenario Comparison</h3>
                <p className="text-xs text-foreground-muted mt-1">
                  Compare KPIs across all scenarios
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {scenarios.length > 0 ? (
                  <div className="space-y-6">
                    {/* KPI Cards */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                      {activeScenario?.kpis && (
                        <>
                          <div className="p-4 bg-surface rounded-xl border border-border">
                            <p className="text-sm text-foreground-muted mb-1">Total Revenue</p>
                            <p className="text-2xl font-bold text-foreground">
                              ${(activeScenario.kpis.totalRevenue / 1000000).toFixed(2)}M
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-xl border border-border">
                            <p className="text-sm text-foreground-muted mb-1">Total Costs</p>
                            <p className="text-2xl font-bold text-foreground">
                              ${(activeScenario.kpis.totalCost / 1000000).toFixed(2)}M
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-xl border border-border">
                            <p className="text-sm text-foreground-muted mb-1">Net Profit</p>
                            <p className={`text-2xl font-bold ${activeScenario.kpis.netProfit >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              ${(activeScenario.kpis.netProfit / 1000000).toFixed(2)}M
                            </p>
                          </div>
                          <div className="p-4 bg-surface rounded-xl border border-border">
                            <p className="text-sm text-foreground-muted mb-1">Growth Rate</p>
                            <p className={`text-2xl font-bold ${activeScenario.kpis.growthRate >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                              {activeScenario.kpis.growthRate >= 0 ? '+' : ''}{activeScenario.kpis.growthRate.toFixed(1)}%
                            </p>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Comparison Charts */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                      <ComparisonChart scenarios={scenarios} metric="revenue" />
                      <ComparisonChart scenarios={scenarios} metric="profit" />
                      <ComparisonChart scenarios={scenarios} metric="growth" />
                    </div>

                    {/* Scenario Summary Table */}
                    <div className="bg-surface rounded-xl border border-border overflow-hidden">
                      <div className="p-4 border-b border-border">
                        <h4 className="font-medium text-foreground">All Scenarios Summary</h4>
                      </div>
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="bg-surface-muted border-b border-border">
                              <th className="text-left px-4 py-3 font-medium text-foreground">Scenario</th>
                              <th className="text-right px-4 py-3 font-medium text-foreground">Revenue</th>
                              <th className="text-right px-4 py-3 font-medium text-foreground">Costs</th>
                              <th className="text-right px-4 py-3 font-medium text-foreground">Profit</th>
                              <th className="text-right px-4 py-3 font-medium text-foreground">Growth</th>
                            </tr>
                          </thead>
                          <tbody>
                            {scenarios.map((scenario) => (
                              <tr
                                key={scenario.id}
                                className={`border-b border-border/50 ${scenario.id === activeScenarioId ? 'bg-brand-600/5' : ''}`}
                              >
                                <td className="px-4 py-3">
                                  <div className="flex items-center gap-2">
                                    <div
                                      className="w-2 h-2 rounded-full"
                                      style={{ backgroundColor: scenario.color }}
                                    />
                                    <span className="text-foreground">{scenario.name}</span>
                                  </div>
                                </td>
                                <td className="text-right px-4 py-3 text-foreground">
                                  ${((scenario.kpis?.totalRevenue || 0) / 1000000).toFixed(2)}M
                                </td>
                                <td className="text-right px-4 py-3 text-foreground">
                                  ${((scenario.kpis?.totalCost || 0) / 1000000).toFixed(2)}M
                                </td>
                                <td className={`text-right px-4 py-3 ${(scenario.kpis?.netProfit || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                  ${((scenario.kpis?.netProfit || 0) / 1000000).toFixed(2)}M
                                </td>
                                <td className={`text-right px-4 py-3 ${(scenario.kpis?.growthRate || 0) >= 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                                  {(scenario.kpis?.growthRate || 0) >= 0 ? '+' : ''}{(scenario.kpis?.growthRate || 0).toFixed(1)}%
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center">
                      <Target className="w-12 h-12 text-foreground-muted mx-auto mb-4 opacity-50" />
                      <p className="text-foreground-muted">Create scenarios to compare</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
