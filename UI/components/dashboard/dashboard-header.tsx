"use client";

import { useAppContext } from '@/lib/app-context';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, RefreshCw, Activity } from 'lucide-react';

export function DashboardHeader() {
  const { 
    systemMode, 
    lastRunTime, 
    atms,
    isRunning,
    setCurrentPage,
    runAnalysis
  } = useAppContext();

  const formatTime = (date: Date | null) => {
    if (!date) return 'Never';
    return date.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getModeLabel = () => {
    switch (systemMode) {
      case 'stable': return 'Stable';
      case 'live': return 'Live';
      case 'csv': return 'CSV';
    }
  };

  const getModeVariant = (): 'default' | 'secondary' | 'destructive' | 'outline' => {
    switch (systemMode) {
      case 'stable': return 'secondary';
      case 'live': return 'destructive';
      case 'csv': return 'outline';
    }
  };

  return (
    <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
      {/* Top Bar */}
      <div className="px-4 lg:px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-gold font-bold text-lg">PayGuard</span>
          <span className="text-danger font-medium text-lg">INTELLIGENCE</span>
          <span className="text-muted-foreground text-xs hidden sm:inline">
            PREDICTIVE ATM INCIDENT INTELLIGENCE PLATFORM - V2.2
          </span>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            <span className={`w-2 h-2 rounded-full ${isRunning ? 'bg-success animate-pulse' : 'bg-warning'}`} />
            <span className="text-muted-foreground hidden sm:inline">
              {isRunning ? 'LIVE' : 'STABLE'} - {formatTime(lastRunTime)}
            </span>
          </div>
          
          <div className="flex items-center gap-2 border border-border rounded-lg p-1">
            <Badge variant={systemMode === 'stable' ? 'default' : 'outline'} className="cursor-pointer">
              Ensemble
            </Badge>
            <Badge variant={getModeVariant()} className="cursor-pointer">
              {getModeLabel()}
            </Badge>
            <Badge variant="outline" className="cursor-pointer hidden sm:inline-flex">
              Demo Mode
            </Badge>
          </div>
        </div>
      </div>

      {/* Alert Banner - show current highest risk ATM */}
      {atms.length > 0 && (
        <div className="px-4 lg:px-6 py-2 bg-danger/10 border-t border-danger/20">
          <div className="flex items-center gap-3 text-sm">
            <span className="text-danger font-medium flex items-center gap-1">
              <Activity className="h-4 w-4" />
              {atms[0].atm_id}
            </span>
            <span className="text-muted-foreground">-</span>
            <span className="text-foreground">{atms[0].location}</span>
            <span className="text-muted-foreground hidden sm:inline">
              {String(atms[0].error_code ?? "Issue").replace(/_/g, " ")} — <span className="text-danger">₹{Math.round(atms[0].exposure ?? 0).toLocaleString()}</span> exposure
            </span>
            <span className="text-muted-foreground hidden md:inline">
              {(atms[0].complaint_count ?? 0).toLocaleString()} complaints · {(atms[0].downtime_minutes ?? 0).toFixed(1)} min downtime ·
              <span className="text-danger"> ({atms.filter((atm) => atm.risk === "HIGH").length} HIGH-risk ATM(s) total)</span>
            </span>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="px-4 lg:px-6 py-2 flex items-center justify-between border-t border-border">
        <button 
          onClick={() => setCurrentPage('launch')}
          className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Control Panel
        </button>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => runAnalysis()}
            className="border-gold text-gold hover:bg-gold hover:text-background"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Run New Analysis
          </Button>
        </div>
      </div>
    </header>
  );
}
