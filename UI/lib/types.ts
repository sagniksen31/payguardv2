export type SystemMode = 'stable' | 'live' | 'csv';

export interface ATMData {
  id?: string;
  atm_id: string;
  location: string;
  transaction_volume: number;
  avg_amount: number;
  downtime_minutes: number;
  complaint_count: number;
  error_code?: string;
  issue_type?: string;
  risk?: 'HIGH' | 'MEDIUM' | 'LOW';
  risk_level?: 'high' | 'medium' | 'low';
  riskScore?: number;
  risk_score?: number;
  last_incident?: string;
  exposure?: number;
  incident_count?: number;
  escalation_probability?: number;
}

export interface Incident {
  id: string;
  type: string;
  count: number;
  atmCount: number;
  downtime: number;
  systemic: boolean;
}

export interface SystemConfig {
  mode: SystemMode;
  numberOfDays: number;
  incidentsPerATM: number;
  forceRetrain: boolean;
}

export interface FleetMetrics {
  totalIncidents: number;
  totalEscalations: number;
  escalationRate: number;
  systemicClusters: number;
  fleetAvailabilityProactive: number;
  fleetImprovementProactivePct: number;
  downtimePrevented: number;
}

export interface RiskDistribution {
  highRiskATMs: number;
  mediumRiskATMs: number;
  lowRiskATMs: number;
  atmsNeedAction: number;
}

export interface IssueDistribution {
  label: string;
  value: number;
  color: string;
}

export interface DailyRiskTrend {
  date: string;
  avgRisk: number;
  highCount: number;
}

export interface AnalyzeApiResponse {
  meta: {
    mode: string;
    n_days: number;
    total_elapsed_sec: number;
    scored_records: number;
    [key: string]: unknown;
  };
  kpis: {
    total_incidents: number;
    total_escalations: number;
    overall_escalation_rate: number;
    [key: string]: unknown;
  };
  availability: {
    fleet_availability_proactive: number;
    fleet_improvement_proactive_pct: number;
    total_downtime_prevented_proactive_min: number;
    daily_trends?: {
      dates: string[];
      reactive: number[];
      automated: number[];
      proactive: number[];
    };
    per_atm?: Array<Record<string, unknown>>;
    [key: string]: unknown;
  };
  root_cause: {
    issue_clusters?: Array<{
      cluster_id: string;
      issue_type: string;
      incident_count: number;
      atm_count: number;
      total_downtime_min: number;
      is_systemic: boolean;
      [key: string]: unknown;
    }>;
    [key: string]: unknown;
  };
  automation_metrics: Record<string, unknown>;
  per_atm_summary: Array<{
    atm_id: string;
    location: string;
    risk_score: number;
    risk: "HIGH" | "MEDIUM" | "LOW";
    downtime_minutes: number;
    complaint_count: number;
    transaction_volume: number;
    avg_amount: number;
    exposure: number;
    issue_type?: string;
    [key: string]: unknown;
  }>;
  scored_batch_sample: Array<Record<string, unknown>>;
}

export interface AvailabilityData {
  strategy: string;
  value: number;
  color: string;
}

export interface SimulationLog {
  id: string;
  timestamp: Date;
  type: 'incident' | 'prediction' | 'automation' | 'alert';
  message: string;
  atm_id?: string;
  severity?: 'info' | 'warning' | 'error' | 'success';
}

export type DashboardTab = 
  | 'overview' 
  | 'high-risk' 
  | 'medium-risk' 
  | 'low-risk' 
  | 'automation' 
  | 'root-cause' 
  | 'availability' 
  | 'feedback';

// Automation Tab Types
export interface AutomationRule {
  id: string;
  name: string;
  status: 'active' | 'paused';
  triggerCount: number;
  successRate: number;
  description: string;
  conditions: string[];
  actions: string[];
  successCount: number;
  failureCount: number;
  avgResolutionTime: number;
  lastTriggered: Date;
}

// Root Cause Tab Types
export interface RootCauseCluster {
  id: string;
  category: 'network' | 'hardware' | 'software' | 'environmental';
  issueCount: number;
  riskLevel: 'high' | 'medium' | 'low';
  description: string;
  topFeatures: { feature: string; contribution: number }[];
  affectedATMs: string[];
  frequencyTrend: { date: string; count: number }[];
}

export interface IdentifiedRootCause {
  id: string;
  issueDescription: string;
  frequency: number;
  severity: 'critical' | 'high' | 'medium' | 'low';
  suggestedFix: string;
  affectedCount: number;
}

// Availability Tab Types
export interface ATMActionRequired {
  atm_id: string;
  location: string;
  issueType: string;
  riskScore: number;
  driftSignal: 'stable' | 'increasing' | 'decreasing';
  downtime: number;
  incidentCount: number;
  escalationProbability: number;
  resolutionMode: 'proactive' | 'reactive' | 'automated';
  historicalIncidents: { date: string; type: string; resolution: string }[];
  riskExplanation: string;
  downtimeImpact: number;
  complaintCount: number;
  revenueImpact: number;
}

// Feedback Types
export interface FeedbackIncidentContext {
  atm_id: string;
  issueType: string;
  riskScore: number;
  escalationProbability: number;
  driftSignal: 'stable' | 'increasing' | 'decreasing';
}

export interface TechnicianFeedback {
  actualIssue: string;
  predictionAccuracy: 'correct' | 'over-predicted' | 'under-predicted';
  actualResolutionTime: number;
  notes: string;
}
