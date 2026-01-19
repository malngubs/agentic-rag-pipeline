/**
 * ============================================================================
 * 📈 KPI CARD - Key Performance Indicator Display
 * ============================================================================
 */

'use client';

import React from 'react';
import { TrendingUp, TrendingDown, Minus, ArrowUp, ArrowDown } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  delta?: number; // Percentage change
  trend?: 'up' | 'down' | 'neutral';
  subtitle?: string;
  icon?: React.ReactNode;
  format?: 'number' | 'currency' | 'percentage';
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  delta,
  trend,
  subtitle,
  icon,
  format = 'number',
}) => {
  const formatValue = (val: string | number) => {
    if (typeof val === 'string') return val;

    switch (format) {
      case 'currency':
        return `$${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      case 'percentage':
        return `${val.toFixed(1)}%`;
      default:
        return val.toLocaleString('en-US');
    }
  };

  const getTrendIcon = () => {
    if (!trend) return null;
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4" />;
      case 'down':
        return <TrendingDown className="w-4 h-4" />;
      default:
        return <Minus className="w-4 h-4" />;
    }
  };

  const getTrendColor = () => {
    if (!trend) return 'text-foreground-muted';
    switch (trend) {
      case 'up':
        return 'text-success';
      case 'down':
        return 'text-error';
      default:
        return 'text-foreground-muted';
    }
  };

  return (
    <div className="glass border border-white/10 p-6 rounded-xl hover:border-brand-600/50 transition-all">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-foreground-muted font-medium">{title}</p>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-brand-600/10 flex items-center justify-center">
            {icon}
          </div>
        )}
      </div>

      {/* Value */}
      <div className="mb-2">
        <p className="text-3xl font-bold text-foreground">{formatValue(value)}</p>
      </div>

      {/* Trend & Delta */}
      <div className="flex items-center gap-2">
        {delta !== undefined && (
          <div className={`flex items-center gap-1 ${getTrendColor()}`}>
            {delta > 0 ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            <span className="text-sm font-medium">{Math.abs(delta).toFixed(1)}%</span>
          </div>
        )}
        {getTrendIcon() && (
          <div className={getTrendColor()}>
            {getTrendIcon()}
          </div>
        )}
        {subtitle && (
          <span className="text-sm text-foreground-muted">{subtitle}</span>
        )}
      </div>
    </div>
  );
};
