"use client";

import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface KPICardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  variant?: 'default' | 'danger' | 'success' | 'warning';
  className?: string;
}

export function KPICard({ 
  title, 
  value, 
  icon, 
  trend, 
  variant = 'default',
  className 
}: KPICardProps) {
  const valueColor = {
    default: 'text-foreground',
    danger: 'text-danger',
    success: 'text-success',
    warning: 'text-warning'
  };

  const borderColor = {
    default: 'border-l-gold',
    danger: 'border-l-danger',
    success: 'border-l-success',
    warning: 'border-l-warning'
  };

  return (
    <Card className={cn(
      'bg-card border border-border border-l-4 p-4 relative overflow-hidden',
      borderColor[variant],
      className
    )}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground mb-2">
            {title}
          </p>
          <p className={cn('text-2xl lg:text-3xl font-bold font-mono', valueColor[variant])}>
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
        </div>
        {icon && (
          <div className={cn('p-2 rounded-lg', {
            'text-gold/60': variant === 'default',
            'text-danger/60': variant === 'danger',
            'text-success/60': variant === 'success',
            'text-warning/60': variant === 'warning',
          })}>
            {icon}
          </div>
        )}
      </div>
      {trend && (
        <div className="absolute bottom-0 right-0 w-16 h-16 opacity-5">
          {trend === 'up' && (
            <svg viewBox="0 0 24 24" className="w-full h-full fill-current">
              <path d="M7 14l5-5 5 5z"/>
            </svg>
          )}
          {trend === 'down' && (
            <svg viewBox="0 0 24 24" className="w-full h-full fill-current">
              <path d="M7 10l5 5 5-5z"/>
            </svg>
          )}
        </div>
      )}
    </Card>
  );
}
