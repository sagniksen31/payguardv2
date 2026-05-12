"use client";

import { useState, Fragment } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useAppContext } from '@/lib/app-context';
import { ChevronDown, ChevronUp, ExternalLink, AlertTriangle, CheckCircle, AlertCircle } from 'lucide-react';

interface ATMTableProps {
  filter?: 'all' | 'high' | 'medium' | 'low';
}

export function ATMTable({ filter = 'all' }: ATMTableProps) {
  const { atms, analysisData } = useAppContext();
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const filteredATMs = filter === 'all'
    ? atms
    : atms.filter(atm => atm.risk_level === filter || atm.risk?.toLowerCase() === filter);

  const getRiskBadge = (level?: string) => {
    switch (level) {
      case 'high':
        return <Badge variant="destructive" className="gap-1"><AlertTriangle className="h-3 w-3" />High</Badge>;
      case 'medium':
        return <Badge className="bg-warning/20 text-warning hover:bg-warning/30 gap-1"><AlertCircle className="h-3 w-3" />Medium</Badge>;
      case 'low':
        return <Badge className="bg-success/20 text-success hover:bg-success/30 gap-1"><CheckCircle className="h-3 w-3" />Low</Badge>;
      default:
        return <Badge variant="outline">Unknown</Badge>;
    }
  };

  const convertToCSV = (rows: Array<Record<string, unknown>>) => {
    if (!rows.length) return '';
    const headers = Object.keys(rows[0]);
    const escape = (value: unknown) => {
      const str = value == null ? '' : String(value);
      if (str.includes(',') || str.includes('"') || str.includes('\n')) {
        return `"${str.replace(/"/g, '""')}"`;
      }
      return str;
    };
    const lines = rows.map((row) => headers.map((h) => escape(row[h])).join(','));
    return [headers.join(','), ...lines].join('\n');
  };

  const downloadReport = (atmId: string) => {
    const source = analysisData?.scored_batch_sample ?? [];
    const eventRows = source
      .filter((row) => String(row.atm_id ?? '') === atmId)
      .map((row) => ({
        atm_id: String(row.atm_id ?? atmId),
        location: String(row.location ?? 'Unknown'),
        risk_score: Number(row.pre_failure_risk_score ?? 0),
        issue_type: String(row.issue_type ?? 'UNKNOWN'),
        downtime_minutes: Number(row.downtime_minutes ?? 0),
        complaint_count: Number(row.complaint_count ?? 0),
        exposure: Number(row.exposure ?? 0),
        error_code: String(row.error_code ?? 'UNKNOWN'),
      }));

    const fallback = atms.find((a) => a.atm_id === atmId);
    const rows = eventRows.length
      ? eventRows
      : fallback
        ? [{
            atm_id: fallback.atm_id,
            location: fallback.location,
            risk_score: Number(fallback.riskScore ?? fallback.risk_score ?? 0),
            issue_type: String(fallback.issue_type ?? 'UNKNOWN'),
            downtime_minutes: Number(fallback.downtime_minutes ?? 0),
            complaint_count: Number(fallback.complaint_count ?? 0),
            exposure: Number(fallback.exposure ?? 0),
            error_code: String(fallback.error_code ?? 'UNKNOWN'),
          }]
        : [];

    const csv = convertToCSV(rows);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${atmId}_full_report.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-foreground">
          ATM Fleet Status {filter !== 'all' && `(${filter.toUpperCase()} Risk)`}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">ATM ID</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Location</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium">Risk</th>
                <th className="text-right py-3 px-4 text-muted-foreground font-medium">Score</th>
                <th className="text-right py-3 px-4 text-muted-foreground font-medium">Downtime</th>
                <th className="text-right py-3 px-4 text-muted-foreground font-medium">Complaints</th>
                <th className="text-right py-3 px-4 text-muted-foreground font-medium">Exposure</th>
                <th className="text-center py-3 px-4 text-muted-foreground font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredATMs.map((atm) => (
                <Fragment key={atm.atm_id}>
                  <tr
                    onClick={() => setExpandedRow(expandedRow === atm.atm_id ? null : atm.atm_id)}
                    className={cn(
                      'border-b border-border cursor-pointer transition-colors hover:bg-secondary/50',
                      expandedRow === atm.atm_id && 'bg-secondary/30'
                    )}
                  >
                    <td className="py-3 px-4">
                      <span className="text-gold font-mono">{atm.atm_id}</span>
                    </td>
                    <td className="py-3 px-4 text-foreground">{atm.location}</td>
                    <td className="py-3 px-4">{getRiskBadge(atm.risk_level)}</td>
                    <td className="py-3 px-4 text-right">
                      <span className={cn(
                        'font-mono',
                        (atm.riskScore ?? atm.risk_score ?? 0) >= 65 ? 'text-danger' :
                        (atm.riskScore ?? atm.risk_score ?? 0) >= 35 ? 'text-warning' : 'text-success'
                      )}>
                        {(atm.riskScore ?? atm.risk_score)?.toFixed(2) || '—'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-muted-foreground">
                      {atm.downtime_minutes} min
                    </td>
                    <td className="py-3 px-4 text-right text-muted-foreground">
                      {atm.complaint_count}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className={cn(
                        'font-mono',
                        atm.exposure && atm.exposure > 50000 ? 'text-danger' : 'text-muted-foreground'
                      )}>
                        ₹{atm.exposure?.toLocaleString() || '—'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        {expandedRow === atm.atm_id ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </td>
                  </tr>
                  {expandedRow === atm.atm_id && (
                    <tr>
                      <td colSpan={8} className="p-4 bg-secondary/20">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                          <div>
                            <h4 className="text-xs uppercase text-muted-foreground mb-2">ATM Details</h4>
                            <div className="space-y-1 text-sm">
                              <p><span className="text-muted-foreground">Transaction Volume:</span> <span className="text-foreground">{atm.transaction_volume}</span></p>
                              <p><span className="text-muted-foreground">Avg Amount:</span> <span className="text-foreground">₹{atm.avg_amount}</span></p>
                              <p><span className="text-muted-foreground">Primary Issue:</span> <span className="text-warning">{atm.issue_type ?? 'Unknown'}</span></p>
                            </div>
                          </div>
                          <div>
                            <h4 className="text-xs uppercase text-muted-foreground mb-2">Risk Explanation</h4>
                            <p className="text-sm text-foreground">
                              {atm.risk_level === 'high' 
                                ? 'High complaint count and extended downtime indicate systemic issues requiring immediate attention.'
                                : atm.risk_level === 'medium'
                                ? 'Moderate risk factors detected. Monitor closely for escalation.'
                                : 'Operating within normal parameters. Continue routine monitoring.'}
                            </p>
                          </div>
                          <div>
                            <h4 className="text-xs uppercase text-muted-foreground mb-2">Recommended Actions</h4>
                            <div className="space-y-2">
                              <Button
                                size="sm"
                                variant="outline"
                                className="w-full justify-start"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  downloadReport(atm.atm_id);
                                }}
                              >
                                <ExternalLink className="h-4 w-4 mr-2" />
                                View Full Report
                              </Button>
                              {atm.risk_level === 'high' && (
                                <Button size="sm" className="w-full bg-danger hover:bg-danger/80">
                                  Create Maintenance Ticket
                                </Button>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
          {filteredATMs.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              No ATMs found with {filter} risk level.
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
