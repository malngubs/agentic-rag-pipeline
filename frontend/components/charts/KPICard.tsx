/**
 * ============================================================================
 * 📊 KPI CARD - MACROCOMM BI PLATFORM
 * ============================================================================
 * 
 * Beautiful KPI cards with trend indicators, animations, and theming.
 */

'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  DollarSign,
  Users,
  ShoppingCart,
  BarChart3,
  Activity,
  Target,
  Zap,
} from 'lucide-react';
import { cn, formatNumber, formatCurrency, formatPercent, formatCompact } from '@/lib/utils';
import type { KPIData } from '@/types';

// =============================================================================
// ICON MAP
// =============================================================================

const iconMap: Record<string, React.ElementType> = {
  dollar: DollarSign,
  users: Users,
  cart: ShoppingCart,
  chart: BarChart3,
  activity: Activity,
  target: Target,
  zap: Zap,
};

// =============================================================================
// KPI CARD COMPONENT
// =============================================================================

interface KPICardProps {
  data: KPIData;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'gradient' | 'outline';
  animate?: boolean;
}

export const KPICard: React.FC<KPICardProps> = ({
  data,
  className,
  size = 'md',
  variant = 'default',
  animate = true,
}) => {
  const {
    title,
    value,
    format = 'number',
    prefix,
    suffix,
    trend,
    icon,
    color,
  } = data;
  
  // Format the value
  const formattedValue = React.useMemo(() => {
    const numValue = typeof value === 'number' ? value : parseFloat(value as string);
    
    if (isNaN(numValue)) return value;
    
    switch (format) {
      case 'currency':
        return formatCurrency(numValue);
      case 'percentage':
        return formatPercent(numValue);
      case 'number':
      default:
        return numValue > 999999 ? formatCompact(numValue) : formatNumber(numValue);
    }
  }, [value, format]);
  
  // Get the icon component
  const IconComponent = icon ? iconMap[icon] || BarChart3 : BarChart3;
  
  // Trend indicator
  const TrendIcon = trend?.direction === 'up' 
    ? TrendingUp 
    : trend?.direction === 'down' 
      ? TrendingDown 
      : Minus;
  
  const trendColor = trend?.direction === 'up'
    ? 'text-success'
    : trend?.direction === 'down'
      ? 'text-error'
      : 'text-foreground-muted';
  
  // Size classes
  const sizeClasses = {
    sm: {
      container: 'p-4',
      title: 'text-xs',
      value: 'text-xl',
      icon: 'w-8 h-8',
      iconInner: 'w-4 h-4',
      trend: 'text-xs',
    },
    md: {
      container: 'p-5',
      title: 'text-sm',
      value: 'text-2xl',
      icon: 'w-10 h-10',
      iconInner: 'w-5 h-5',
      trend: 'text-sm',
    },
    lg: {
      container: 'p-6',
      title: 'text-sm',
      value: 'text-3xl',
      icon: 'w-12 h-12',
      iconInner: 'w-6 h-6',
      trend: 'text-sm',
    },
  };
  
  const sizes = sizeClasses[size];
  
  // Variant classes
  const variantClasses = {
    default: 'bg-surface border border-border',
    gradient: 'bg-gradient-to-br from-surface to-surface-hover border border-border',
    outline: 'bg-transparent border-2 border-border',
  };
  
  // Custom color or brand color
  const accentColor = color || 'var(--color-brand-600)';
  
  return (
    <motion.div
      initial={animate ? { opacity: 0, y: 20 } : false}
      animate={animate ? { opacity: 1, y: 0 } : false}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={cn(
        'rounded-xl transition-all duration-200 hover:shadow-card-hover group',
        variantClasses[variant],
        sizes.container,
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        {/* Icon */}
        <div
          className={cn(
            'rounded-lg flex items-center justify-center transition-colors',
            sizes.icon
          )}
          style={{
            backgroundColor: `color-mix(in srgb, ${accentColor} 15%, transparent)`,
          }}
        >
          <IconComponent
            className={cn(sizes.iconInner)}
            style={{ color: accentColor }}
          />
        </div>
        
        {/* Trend */}
        {trend && (
          <div className={cn('flex items-center gap-1', trendColor, sizes.trend)}>
            <TrendIcon className="w-4 h-4" />
            <span className="font-medium">
              {trend.value > 0 ? '+' : ''}{trend.value}%
            </span>
          </div>
        )}
      </div>
      
      {/* Value */}
      <div className="mb-1">
        <span
          className={cn(
            'font-display font-bold text-foreground',
            sizes.value
          )}
        >
          {prefix}
          {formattedValue}
          {suffix}
        </span>
      </div>
      
      {/* Title */}
      <div className={cn('text-foreground-muted font-medium', sizes.title)}>
        {title}
      </div>
      
      {/* Trend period */}
      {trend?.period && (
        <div className="mt-2 text-xs text-foreground-muted">
          vs {trend.period}
        </div>
      )}
      
      {/* Decorative gradient line */}
      <div
        className="absolute bottom-0 left-0 right-0 h-1 rounded-b-xl opacity-0 group-hover:opacity-100 transition-opacity"
        style={{
          background: `linear-gradient(90deg, ${accentColor}, transparent)`,
        }}
      />
    </motion.div>
  );
};

// =============================================================================
// KPI GRID COMPONENT
// =============================================================================

interface KPIGridProps {
  kpis: KPIData[];
  columns?: 2 | 3 | 4;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export const KPIGrid: React.FC<KPIGridProps> = ({
  kpis,
  columns = 4,
  size = 'md',
  className,
}) => {
  const gridCols = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-4',
  };
  
  return (
    <div className={cn('grid gap-4', gridCols[columns], className)}>
      {kpis.map((kpi, index) => (
        <motion.div
          key={kpi.id || index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
        >
          <KPICard data={kpi} size={size} />
        </motion.div>
      ))}
    </div>
  );
};

// =============================================================================
// MINI KPI (for inline display)
// =============================================================================

interface MiniKPIProps {
  label: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export const MiniKPI: React.FC<MiniKPIProps> = ({
  label,
  value,
  trend,
  className,
}) => {
  const TrendIcon = trend === 'up' 
    ? TrendingUp 
    : trend === 'down' 
      ? TrendingDown 
      : null;
  
  const trendColor = trend === 'up' ? 'text-success' : 'text-error';
  
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <span className="text-sm text-foreground-muted">{label}:</span>
      <span className="text-sm font-semibold text-foreground">{value}</span>
      {TrendIcon && (
        <TrendIcon className={cn('w-3 h-3', trendColor)} />
      )}
    </div>
  );
};

export default KPICard;
