"use client";

import { useState } from 'react';
import { useAppContext } from '@/lib/app-context';
import { DashboardHeader } from './dashboard-header';
import { DashboardTabs } from './dashboard-tabs';
import { KPICard } from './kpi-card';
import { IssueDistributionChart, DailyRiskTrendChart, AvailabilityChart } from './analytics-charts';
import { ATMTable } from './atm-table';
import { SimulationConsole } from './simulation-console';
import { FeedbackPanel } from './feedback-panel';
import { AutomationTab } from './automation-tab';
import { RootCauseTab } from './root-cause-tab';
import { AvailabilityTab } from './availability-tab';
import { Badge } from '@/components/ui/badge';
import type { DashboardTab } from '@/lib/types';
import { 
  AlertTriangle, 
  TrendingUp, 
  Percent, 
  Layers, 
  Target,
  RefreshCw,
  CheckCircle,
  Zap,
  Clock
} from 'lucide-react';

export function DashboardPage() {
  const { 
    fleetMetrics, 
    riskDistribution, 
    systemMode, 
    isRunning
  } = useAppContext();
  const [activeTab, setActiveTab] = useState<DashboardTab>('overview');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'high-risk':
        return <ATMTable filter="high" />;
      case 'medium-risk':
        return <ATMTable filter="medium" />;
      case 'low-risk':
        return <ATMTable filter="low" />;
      case 'automation':
        return <AutomationTab />;
      case 'root-cause':
        return <RootCauseTab />;
      case 'availability':
        return <AvailabilityTab />;
      case 'feedback':
        return <FeedbackPanel />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <DashboardHeader />
      <DashboardTabs activeTab={activeTab} onTabChange={setActiveTab} />
      
      {/* Historical Performance Banner */}
      <div className="px-4 lg:px-6 py-3 border-b border-border flex items-center gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-gold" />
          <span className="font-medium text-foreground">Historical Performance</span>
        </div>
        <span className="text-muted-foreground">—</span>
        <span className="text-muted-foreground">Full 60-day dataset</span>
        <span className="text-muted-foreground">·</span>
        <span className="text-gold font-mono">{fleetMetrics.totalIncidents.toLocaleString()}</span>
        <span className="text-muted-foreground">incidents</span>
        <span className="text-muted-foreground">·</span>
        <span className="text-muted-foreground">Source: historical_logs.csv</span>
      </div>

      <main className="p-4 lg:p-6">
        {renderTabContent()}
      </main>
    </div>
  );
}

function OverviewTab() {
  const { fleetMetrics, riskDistribution, systemMode, isRunning, atms } = useAppContext();
  const totalAtms = atms.length;

  return (
    <div className="space-y-6">
      {/* Fleet Performance Section */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-5 bg-gold rounded" />
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Fleet Performance (Historical)
          </h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <KPICard
            title="Total Incidents"
            value={fleetMetrics.totalIncidents}
            icon={<AlertTriangle className="h-5 w-5" />}
            variant="default"
          />
          <KPICard
            title="Total Escalations"
            value={fleetMetrics.totalEscalations}
            icon={<TrendingUp className="h-5 w-5" />}
            variant="danger"
          />
          <KPICard
            title="Escalation Rate"
            value={`${(fleetMetrics.escalationRate * 100).toFixed(1)}%`}
            icon={<Percent className="h-5 w-5" />}
            variant="default"
          />
          <KPICard
            title="Systemic Clusters"
            value={fleetMetrics.systemicClusters}
            icon={<Layers className="h-5 w-5" />}
            variant="default"
          />
          <KPICard
            title="Fleet Availability (Proactive)"
            value={`${(fleetMetrics.fleetAvailabilityProactive * 100).toFixed(2)}%`}
            icon={<Target className="h-5 w-5" />}
            variant="success"
          />
        </div>
      </section>

      {/* Current System State Banner */}
      <div className="bg-secondary/30 border border-border rounded-lg px-4 py-3 flex items-center gap-3">
        <Zap className="h-4 w-4 text-gold" />
        <span className="text-sm font-medium text-gold">Current System State</span>
        <span className="text-sm text-muted-foreground">
          Event-level scoring for analytics · {totalAtms} unique ATMs in aggregated fleet view
        </span>
        {isRunning && (
          <Badge className="ml-auto bg-success/20 text-success animate-pulse">
            <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
            Live Updates
          </Badge>
        )}
      </div>

      {/* Current Risk Distribution */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-5 bg-gold rounded" />
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Current Risk Distribution (Per ATM)
          </h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
          <KPICard
            title="High Risk ATMs"
            value={riskDistribution.highRiskATMs}
            icon={<AlertTriangle className="h-5 w-5" />}
            variant="danger"
          />
          <KPICard
            title="Medium Risk ATMs"
            value={riskDistribution.mediumRiskATMs}
            icon={<RefreshCw className="h-5 w-5" />}
            variant="warning"
          />
          <KPICard
            title="Low Risk ATMs"
            value={riskDistribution.lowRiskATMs}
            icon={<CheckCircle className="h-5 w-5" />}
            variant="success"
          />
          <KPICard
            title="Availability Improvement"
            value={`+${fleetMetrics.fleetImprovementProactivePct.toFixed(3)}pp`}
            icon={<Target className="h-5 w-5" />}
            variant="success"
          />
          <KPICard
            title="ATMs Need Action"
            value={riskDistribution.atmsNeedAction}
            icon={<Clock className="h-5 w-5" />}
            variant="warning"
          />
        </div>
      </section>

      {/* Analytics Section */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <div className="w-1 h-5 bg-gold rounded" />
          <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Analytics
          </h2>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <IssueDistributionChart />
          <DailyRiskTrendChart />
          <AvailabilityChart />
        </div>
      </section>

      {/* Simulation Console (show in live mode) */}
      {systemMode === 'live' && (
        <section>
          <div className="flex items-center gap-2 mb-4">
            <div className="w-1 h-5 bg-gold rounded" />
            <h2 className="text-sm font-medium uppercase tracking-wide text-muted-foreground">
              Live Simulation
            </h2>
          </div>
          <SimulationConsole />
        </section>
      )}

      {/* ATM Table */}
      <section>
        <ATMTable filter="all" />
      </section>
    </div>
  );
}






