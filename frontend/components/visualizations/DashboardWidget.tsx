/**
 * ============================================================================
 * 📊 DASHBOARD WIDGET - Multi-Chart Dashboard Display
 * ============================================================================
 */

'use client';

import React from 'react';
import { ChartWidget } from './ChartWidget';
import { KPICard } from './KPICard';
import { Download, Maximize2 } from 'lucide-react';

interface DashboardConfig {
  title: string;
  description?: string;
  kpis?: Array<{
    title: string;
    value: string | number;
    delta?: number;
    trend?: 'up' | 'down' | 'neutral';
    format?: 'number' | 'currency' | 'percentage';
  }>;
  charts?: Array<{
    data: any;
    title?: string;
    description?: string;
    width?: number; // Grid columns (1-12)
  }>;
}

interface DashboardWidgetProps {
  dashboard: DashboardConfig;
}

export const DashboardWidget: React.FC<DashboardWidgetProps> = ({ dashboard }) => {
  const handleExport = () => {
    // TODO: Implement dashboard export
    console.log('Exporting dashboard:', dashboard.title);
  };

  return (
    <div className="space-y-6">
      {/* Dashboard Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold text-foreground mb-2">{dashboard.title}</h2>
          {dashboard.description && (
            <p className="text-foreground-muted">{dashboard.description}</p>
          )}
        </div>
        <button
          onClick={handleExport}
          className="glossy-button px-4 py-2 rounded-lg text-white flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
      </div>

      {/* KPI Cards */}
      {dashboard.kpis && dashboard.kpis.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {dashboard.kpis.map((kpi, index) => (
            <KPICard key={index} {...kpi} />
          ))}
        </div>
      )}

      {/* Charts Grid */}
      {dashboard.charts && dashboard.charts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {dashboard.charts.map((chart, index) => (
            <div
              key={index}
              className={chart.width === 12 ? 'lg:col-span-2' : ''}
            >
              <ChartWidget
                chartData={chart.data}
                title={chart.title}
                description={chart.description}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
