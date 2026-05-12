"use client";

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, TrendingUp } from 'lucide-react';
import { useAppContext } from '@/lib/app-context';

export function RootCauseTab() {
  const { analysisData } = useAppContext();
  const clusters = analysisData?.root_cause?.issue_clusters ?? [];

  return (
    <div className="space-y-6">
      {/* Summary Stats by issue type */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(
          clusters.reduce<Record<string, number>>((acc, cluster) => {
            const key = String(cluster.issue_type ?? "unknown");
            acc[key] = (acc[key] ?? 0) + Number(cluster.incident_count ?? 0);
            return acc;
          }, {})
        )
          .slice(0, 4)
          .map(([issueType, count]) => (
            <Card key={issueType} className="bg-card border-border">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground uppercase tracking-wide">{issueType.replace(/_/g, " ")}</p>
                    <p className="text-2xl font-bold text-foreground mt-1">{count.toLocaleString()}</p>
                  </div>
                  <AlertTriangle className="h-5 w-5 text-warning" />
                </div>
              </CardContent>
            </Card>
          ))}
      </div>

      {/* Cluster Analysis */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-foreground flex items-center gap-2">
            <TrendingUp className="h-5 w-5 text-gold" />
            Cluster Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Cluster ID</th>
                  <th className="text-left py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Issue Type</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Issue Count</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">ATMs</th>
                  <th className="text-right py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Downtime</th>
                  <th className="text-center py-3 px-4 text-xs font-medium text-muted-foreground uppercase tracking-wide">Systemic</th>
                </tr>
              </thead>
              <tbody>
                {clusters.map((cluster) => (
                  <tr key={cluster.cluster_id} className="border-b border-border">
                    <td className="py-3 px-4 text-sm font-mono text-gold">{cluster.cluster_id}</td>
                    <td className="py-3 px-4 text-sm text-foreground">{String(cluster.issue_type).replace(/_/g, " ")}</td>
                    <td className="py-3 px-4 text-sm text-right">{Number(cluster.incident_count ?? 0).toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm text-right">{Number(cluster.atm_count ?? 0).toLocaleString()}</td>
                    <td className="py-3 px-4 text-sm text-right">{Number(cluster.total_downtime_min ?? 0).toFixed(0)} min</td>
                    <td className="py-3 px-4 text-center">
                      <Badge className={cluster.is_systemic ? "bg-danger/20 text-danger" : "bg-secondary text-muted-foreground"}>
                        {cluster.is_systemic ? "YES" : "NO"}
                      </Badge>
                    </td>
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
