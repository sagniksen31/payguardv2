"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Zap,
  Clock,
  TrendingUp
} from 'lucide-react';
import { useAppContext } from '@/lib/app-context';

export function AutomationTab() {
  const { analysisData } = useAppContext();
  const metrics = analysisData?.automation_metrics ?? {};

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Auto Resolved</p>
                <p className="text-2xl font-bold text-success mt-1">
                  {Number(metrics.auto_resolved_count ?? 0).toLocaleString()}
                </p>
              </div>
              <Zap className="h-5 w-5 text-success" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Auto Attempted</p>
                <p className="text-2xl font-bold text-gold mt-1">
                  {Number(metrics.auto_attempted_count ?? 0).toLocaleString()}
                </p>
              </div>
              <Zap className="h-5 w-5 text-gold" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Manual Reduction</p>
                <p className="text-2xl font-bold text-foreground mt-1">
                  {Number(metrics.manual_reduction_pct ?? 0).toFixed(1)}%
                </p>
              </div>
              <TrendingUp className="h-5 w-5 text-success" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wide">Avg Auto Time</p>
                <p className="text-2xl font-bold text-warning mt-1">
                  {Number(metrics.avg_auto_time_sec ?? 0).toFixed(1)}s
                </p>
              </div>
              <Clock className="h-5 w-5 text-warning" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Automation Metrics Table */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground flex items-center gap-2">
            <Zap className="h-5 w-5 text-gold" />
            Automation Performance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(metrics).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between rounded-lg border border-border bg-secondary/20 p-3">
                <span className="text-xs uppercase tracking-wide text-muted-foreground">{key.replace(/_/g, " ")}</span>
                <span className="text-sm font-mono text-foreground">{String(value)}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
