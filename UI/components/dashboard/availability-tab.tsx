"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle } from 'lucide-react';
import { AvailabilityChart } from './analytics-charts';
import { useAppContext } from '@/lib/app-context';

export function AvailabilityTab() {
  const { analysisData, atms, fleetMetrics } = useAppContext();
  const requiringAction = atms.filter((atm) => atm.risk === 'HIGH');
  const perAtm = analysisData?.availability?.per_atm ?? [];

  return (
    <div className="space-y-6">
      {/* Summary Stats and Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AvailabilityChart />
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="text-foreground">Uptime Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <span className="text-muted-foreground">Fleet Average Uptime</span>
                <span className="text-success font-mono text-lg">{(fleetMetrics.fleetAvailabilityProactive * 100).toFixed(2)}%</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <span className="text-muted-foreground">Availability Improvement</span>
                <span className="text-gold font-mono text-lg">+{fleetMetrics.fleetImprovementProactivePct.toFixed(3)}pp</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <span className="text-muted-foreground">Downtime Prevented</span>
                <span className="text-foreground font-mono text-lg">{fleetMetrics.downtimePrevented.toFixed(0)} min</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-secondary/30 rounded-lg">
                <span className="text-muted-foreground">ATMs Requiring Action</span>
                <span className="text-warning font-mono text-lg">{requiringAction.length}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ATMs Requiring Action Table */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            ATMs Requiring Action
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">ATM ID</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Location</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Reactive</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Proactive</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Improvement</th>
                </tr>
              </thead>
              <tbody>
                {perAtm.map((row, idx) => (
                  <tr key={`${String(row.atm_id)}-${idx}`} className="border-b border-border">
                    <td className="py-3 px-4 text-sm font-mono text-gold">{String(row.atm_id ?? "-")}</td>
                    <td className="py-3 px-4 text-sm text-foreground">{String(row.location ?? "-")}</td>
                    <td className="py-3 px-4 text-sm text-right">{(Number(row.availability_reactive ?? 0) * 100).toFixed(2)}%</td>
                    <td className="py-3 px-4 text-sm text-right">{(Number(row.availability_proactive ?? 0) * 100).toFixed(2)}%</td>
                    <td className="py-3 px-4 text-sm text-right">+{Number(row.improvement_proactive_vs_reactive ?? 0).toFixed(3)}pp</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
