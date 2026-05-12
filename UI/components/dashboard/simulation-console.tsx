"use client";

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAppContext } from '@/lib/app-context';
import { cn } from '@/lib/utils';
import { Activity, AlertTriangle, Zap, Bell, Info } from 'lucide-react';

export function SimulationConsole() {
  const { simulationLogs, isRunning } = useAppContext();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [simulationLogs]);

  const getLogIcon = (type: string) => {
    switch (type) {
      case 'incident': return <AlertTriangle className="h-3 w-3" />;
      case 'prediction': return <Activity className="h-3 w-3" />;
      case 'automation': return <Zap className="h-3 w-3" />;
      case 'alert': return <Bell className="h-3 w-3" />;
      default: return <Info className="h-3 w-3" />;
    }
  };

  const getLogColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'text-danger';
      case 'warning': return 'text-warning';
      case 'success': return 'text-success';
      default: return 'text-info';
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-IN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-foreground flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Live Simulation Console
          </CardTitle>
          {isRunning && (
            <Badge className="bg-success/20 text-success animate-pulse">
              <span className="w-2 h-2 rounded-full bg-success mr-2" />
              LIVE
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div 
          ref={scrollRef}
          className="h-64 overflow-y-auto font-mono text-xs bg-background rounded-lg p-3 border border-border"
        >
          {simulationLogs.length === 0 ? (
            <div className="text-muted-foreground text-center py-8">
              {isRunning ? 'Waiting for events...' : 'Start simulation to see live logs'}
            </div>
          ) : (
            <div className="space-y-1">
              {simulationLogs.map((log) => (
                <div 
                  key={log.id}
                  className={cn(
                    'flex items-start gap-2 py-1 animate-in fade-in slide-in-from-top-1 duration-300',
                    getLogColor(log.severity || 'info')
                  )}
                >
                  <span className="text-muted-foreground shrink-0">
                    [{formatTime(log.timestamp)}]
                  </span>
                  <span className="shrink-0">
                    {getLogIcon(log.type)}
                  </span>
                  <span className="text-foreground">{log.message}</span>
                  {log.atm_id && (
                    <Badge variant="outline" className="text-[10px] py-0 px-1">
                      {log.atm_id}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
