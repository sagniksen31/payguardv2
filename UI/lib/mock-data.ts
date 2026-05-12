import type { 
  ATMData
} from './types';

export const mockATMs: ATMData[] = [
  {
    atm_id: 'ATM-1097',
    location: 'Delhi CP 2',
    transaction_volume: 1250,
    avg_amount: 5600,
    downtime_minutes: 50.4,
    complaint_count: 23,
    error_code: 'E401',
    risk_level: 'high',
    risk_score: 0.87,
    last_incident: 'Card Declined',
    exposure: 85980
  },
  {
    atm_id: 'ATM-2045',
    location: 'Mumbai Andheri',
    transaction_volume: 980,
    avg_amount: 4200,
    downtime_minutes: 12.5,
    complaint_count: 5,
    error_code: 'E102',
    risk_level: 'low',
    risk_score: 0.23,
    last_incident: 'Network Timeout',
    exposure: 12500
  },
  {
    atm_id: 'ATM-3012',
    location: 'Bangalore Koramangala',
    transaction_volume: 1500,
    avg_amount: 6800,
    downtime_minutes: 8.2,
    complaint_count: 3,
    error_code: 'E201',
    risk_level: 'low',
    risk_score: 0.18,
    last_incident: 'Auth Timeout',
    exposure: 8200
  },
  {
    atm_id: 'ATM-4089',
    location: 'Chennai T Nagar',
    transaction_volume: 870,
    avg_amount: 3900,
    downtime_minutes: 15.8,
    complaint_count: 8,
    error_code: 'E301',
    risk_level: 'low',
    risk_score: 0.31,
    last_incident: 'Cash Low',
    exposure: 15800
  }
];

export const mockIncidents: any[] = [
  {
    id: 'INC-001',
    atm_id: 'ATM-1097',
    location: 'Delhi CP 2',
    type: 'Card Declined',
    severity: 'high',
    timestamp: new Date(),
    description: 'Multiple card decline errors detected',
    status: 'escalated',
    exposure: 85980,
    complaints: 23,
    downtime: 50.4
  },
  {
    id: 'INC-002',
    atm_id: 'ATM-2045',
    location: 'Mumbai Andheri',
    type: 'Network Timeout',
    severity: 'low',
    timestamp: new Date(Date.now() - 3600000),
    description: 'Intermittent network connectivity issues',
    status: 'open',
    exposure: 12500,
    complaints: 5,
    downtime: 12.5
  }
];

export const mockFleetMetrics: any = {
  totalIncidents: 27864,
  totalEscalations: 10766,
  escalationRate: 38.6,
  systemicClusters: 50,
  modelROCAUC: 0.8191
};

export const mockRiskDistribution: any = {
  highRiskATMs: 1,
  mediumRiskATMs: 0,
  lowRiskATMs: 3,
  avgPrecision: 0.5275,
  atmsNeedAction: 1
};

export const mockIssueDistribution: any[] = [
  { label: 'Card Declined', value: 28, color: '#d4a84b' },
  { label: 'Auth Timeout', value: 24, color: '#3b82f6' },
  { label: 'Network Failure', value: 18, color: '#ef4444' },
  { label: 'Cash Dispense', value: 14, color: '#22c55e' },
  { label: 'Other', value: 16, color: '#737373' }
];

export const mockDailyRiskTrend: any[] = [
  { date: 'Apr 01', avgRisk: 8, highCount: 0 },
  { date: 'Apr 02', avgRisk: 10, highCount: 0 },
  { date: 'Apr 03', avgRisk: 14, highCount: 0 },
  { date: 'Apr 04', avgRisk: 12, highCount: 0 },
  { date: 'Apr 05', avgRisk: 18, highCount: 1 },
  { date: 'Apr 06', avgRisk: 22, highCount: 1 },
  { date: 'Apr 07', avgRisk: 16, highCount: 2 },
  { date: 'Apr 08', avgRisk: 25, highCount: 2 },
  { date: 'Apr 09', avgRisk: 28, highCount: 2 }
];

export const mockAvailabilityData: any[] = [
  { strategy: 'Reactive', value: 78, color: '#ef4444' },
  { strategy: 'Automated', value: 92, color: '#d4a84b' },
  { strategy: 'Proactive', value: 65, color: '#22c55e' }
];

// Automation Rules Data
export const mockAutomationRules: any[] = [
  {
    id: 'AR-001',
    name: 'High Risk Auto-Escalation',
    status: 'active',
    triggerCount: 1247,
    successRate: 94.2,
    description: 'Automatically escalate incidents when risk score exceeds threshold and complaint count is high.',
    conditions: ['Risk Score > 0.7', 'Complaint Count > 10', 'Downtime > 30 min'],
    actions: ['Create escalation ticket', 'Notify regional manager', 'Assign priority technician'],
    successCount: 1175,
    failureCount: 72,
    avgResolutionTime: 23,
    lastTriggered: new Date(Date.now() - 1800000)
  },
  {
    id: 'AR-002',
    name: 'Predictive Maintenance Scheduler',
    status: 'active',
    triggerCount: 856,
    successRate: 87.5,
    description: 'Schedule preventive maintenance for ATMs with predicted failure probability above threshold.',
    conditions: ['Failure Probability > 60%', 'Days Since Maintenance > 45', 'Transaction Volume > 500/day'],
    actions: ['Schedule maintenance window', 'Order replacement parts', 'Notify maintenance team'],
    successCount: 749,
    failureCount: 107,
    avgResolutionTime: 45,
    lastTriggered: new Date(Date.now() - 7200000)
  },
  {
    id: 'AR-003',
    name: 'Cash Replenishment Alert',
    status: 'active',
    triggerCount: 2341,
    successRate: 98.1,
    description: 'Trigger cash replenishment alerts based on transaction patterns and current cash levels.',
    conditions: ['Cash Level < 20%', 'Projected Depletion < 4 hours', 'High Traffic Period'],
    actions: ['Alert cash management team', 'Update replenishment schedule', 'Notify branch supervisor'],
    successCount: 2297,
    failureCount: 44,
    avgResolutionTime: 35,
    lastTriggered: new Date(Date.now() - 900000)
  },
  {
    id: 'AR-004',
    name: 'Network Failover Protocol',
    status: 'paused',
    triggerCount: 423,
    successRate: 76.8,
    description: 'Automatically switch to backup network when primary connection fails.',
    conditions: ['Connection Timeout > 3 attempts', 'Packet Loss > 15%', 'Latency > 500ms'],
    actions: ['Switch to backup network', 'Log connectivity event', 'Alert network operations'],
    successCount: 325,
    failureCount: 98,
    avgResolutionTime: 5,
    lastTriggered: new Date(Date.now() - 86400000)
  },
  {
    id: 'AR-005',
    name: 'Security Anomaly Response',
    status: 'active',
    triggerCount: 189,
    successRate: 91.5,
    description: 'Detect and respond to unusual transaction patterns that may indicate security threats.',
    conditions: ['Transaction Pattern Anomaly Score > 0.8', 'Multiple Failed Auth > 5', 'Unusual Time Window'],
    actions: ['Temporary transaction hold', 'Security team alert', 'Enhanced monitoring mode'],
    successCount: 173,
    failureCount: 16,
    avgResolutionTime: 12,
    lastTriggered: new Date(Date.now() - 3600000)
  }
];

// Root Cause Clusters Data
export const mockRootCauseClusters: any[] = [
  {
    id: 'RC-001',
    category: 'network',
    issueCount: 8432,
    riskLevel: 'high',
    description: 'Network connectivity issues caused by ISP instability during peak hours, affecting transaction processing and authentication services.',
    topFeatures: [
      { feature: 'Peak Hour Load', contribution: 34 },
      { feature: 'ISP Reliability Score', contribution: 28 },
      { feature: 'Bandwidth Utilization', contribution: 22 },
      { feature: 'DNS Response Time', contribution: 16 }
    ],
    affectedATMs: ['ATM-1097', 'ATM-2045', 'ATM-4089'],
    frequencyTrend: [
      { date: 'Apr 01', count: 120 },
      { date: 'Apr 02', count: 145 },
      { date: 'Apr 03', count: 132 },
      { date: 'Apr 04', count: 168 },
      { date: 'Apr 05', count: 189 },
      { date: 'Apr 06', count: 156 },
      { date: 'Apr 07', count: 142 }
    ]
  },
  {
    id: 'RC-002',
    category: 'hardware',
    issueCount: 5621,
    riskLevel: 'medium',
    description: 'Card reader mechanism degradation due to high usage volume and environmental factors affecting magnetic stripe reading accuracy.',
    topFeatures: [
      { feature: 'Card Reader Age', contribution: 38 },
      { feature: 'Transaction Volume', contribution: 27 },
      { feature: 'Humidity Level', contribution: 20 },
      { feature: 'Cleaning Frequency', contribution: 15 }
    ],
    affectedATMs: ['ATM-1097', 'ATM-3012'],
    frequencyTrend: [
      { date: 'Apr 01', count: 85 },
      { date: 'Apr 02', count: 92 },
      { date: 'Apr 03', count: 78 },
      { date: 'Apr 04', count: 95 },
      { date: 'Apr 05', count: 110 },
      { date: 'Apr 06', count: 98 },
      { date: 'Apr 07', count: 87 }
    ]
  },
  {
    id: 'RC-003',
    category: 'software',
    issueCount: 4127,
    riskLevel: 'medium',
    description: 'Authentication timeout issues related to core banking system response delays during high-load periods.',
    topFeatures: [
      { feature: 'CBS Response Time', contribution: 42 },
      { feature: 'Concurrent Sessions', contribution: 25 },
      { feature: 'Memory Utilization', contribution: 18 },
      { feature: 'Cache Hit Rate', contribution: 15 }
    ],
    affectedATMs: ['ATM-2045', 'ATM-3012', 'ATM-4089'],
    frequencyTrend: [
      { date: 'Apr 01', count: 65 },
      { date: 'Apr 02', count: 72 },
      { date: 'Apr 03', count: 58 },
      { date: 'Apr 04', count: 81 },
      { date: 'Apr 05', count: 76 },
      { date: 'Apr 06', count: 69 },
      { date: 'Apr 07', count: 74 }
    ]
  },
  {
    id: 'RC-004',
    category: 'environmental',
    issueCount: 2845,
    riskLevel: 'low',
    description: 'Temperature fluctuations in outdoor ATM enclosures affecting hardware performance and reliability.',
    topFeatures: [
      { feature: 'Ambient Temperature', contribution: 45 },
      { feature: 'HVAC Status', contribution: 28 },
      { feature: 'Enclosure Type', contribution: 17 },
      { feature: 'Geographic Location', contribution: 10 }
    ],
    affectedATMs: ['ATM-4089'],
    frequencyTrend: [
      { date: 'Apr 01', count: 35 },
      { date: 'Apr 02', count: 42 },
      { date: 'Apr 03', count: 38 },
      { date: 'Apr 04', count: 51 },
      { date: 'Apr 05', count: 48 },
      { date: 'Apr 06', count: 44 },
      { date: 'Apr 07', count: 39 }
    ]
  }
];

// Identified Root Causes Data
export const mockIdentifiedRootCauses: any[] = [
  {
    id: 'IRC-001',
    issueDescription: 'ISP bandwidth throttling during peak business hours (10AM-2PM)',
    frequency: 342,
    severity: 'critical',
    suggestedFix: 'Upgrade to dedicated fiber connection with SLA guarantees. Consider secondary ISP for failover.',
    affectedCount: 3
  },
  {
    id: 'IRC-002',
    issueDescription: 'Card reader head wear causing intermittent read failures',
    frequency: 187,
    severity: 'high',
    suggestedFix: 'Schedule card reader head replacement for ATMs exceeding 50,000 monthly transactions.',
    affectedCount: 2
  },
  {
    id: 'IRC-003',
    issueDescription: 'Core banking timeout during batch processing windows',
    frequency: 156,
    severity: 'high',
    suggestedFix: 'Implement request queuing with retry logic. Coordinate with CBS team for batch window optimization.',
    affectedCount: 3
  },
  {
    id: 'IRC-004',
    issueDescription: 'Cash dispenser mechanism jamming due to note quality',
    frequency: 89,
    severity: 'medium',
    suggestedFix: 'Implement stricter note quality checks during replenishment. Adjust dispenser tension settings.',
    affectedCount: 1
  },
  {
    id: 'IRC-005',
    issueDescription: 'Thermal paper sensor misalignment in receipt printer',
    frequency: 67,
    severity: 'low',
    suggestedFix: 'Include sensor calibration in routine maintenance checklist.',
    affectedCount: 2
  }
];

// ATMs Requiring Action Data
export const mockATMsRequiringAction: any[] = [
  {
    atm_id: 'ATM-1097',
    location: 'Delhi CP 2',
    issueType: 'Card Declined / High Complaints',
    riskScore: 0.87,
    driftSignal: 'increasing',
    downtime: 50.4,
    incidentCount: 23,
    escalationProbability: 0.92,
    resolutionMode: 'reactive',
    historicalIncidents: [
      { date: '2024-04-08', type: 'Card Declined', resolution: 'Card reader cleaned' },
      { date: '2024-04-06', type: 'Network Timeout', resolution: 'ISP notified' },
      { date: '2024-04-03', type: 'Auth Timeout', resolution: 'CBS restarted' },
      { date: '2024-04-01', type: 'Card Declined', resolution: 'Magnetic head replaced' }
    ],
    riskExplanation: 'High complaint count (23) combined with increasing downtime trend indicates deteriorating card reader mechanism. Network instability exacerbating authentication failures.',
    downtimeImpact: 85980,
    complaintCount: 23,
    revenueImpact: 125000
  },
  {
    atm_id: 'ATM-4089',
    location: 'Chennai T Nagar',
    issueType: 'Cash Low / Environmental',
    riskScore: 0.31,
    driftSignal: 'stable',
    downtime: 15.8,
    incidentCount: 8,
    escalationProbability: 0.35,
    resolutionMode: 'proactive',
    historicalIncidents: [
      { date: '2024-04-07', type: 'Cash Low', resolution: 'Replenishment completed' },
      { date: '2024-04-04', type: 'Temperature Alert', resolution: 'HVAC serviced' }
    ],
    riskExplanation: 'Moderate risk due to environmental factors. Temperature fluctuations resolved with HVAC maintenance. Cash management on schedule.',
    downtimeImpact: 15800,
    complaintCount: 8,
    revenueImpact: 32000
  }
];

export const errorCodes = [
  'E101 - Connection Timeout',
  'E102 - Network Failure',
  'E201 - Authentication Error',
  'E301 - Cash Dispense Failure',
  'E401 - Card Reader Error',
  'E501 - Hardware Malfunction'
];

export const incidentTypes = [
  'Card Declined',
  'Auth Timeout',
  'Network Failure',
  'Cash Dispense Error',
  'Hardware Fault',
  'Security Alert'
];

export function generateRandomIncident(): any {
  const atm = mockATMs[Math.floor(Math.random() * mockATMs.length)];
  const type = incidentTypes[Math.floor(Math.random() * incidentTypes.length)];
  const severity =
    Math.random() > 0.7 ? 'high' : Math.random() > 0.4 ? 'medium' : 'low';
  
  return {
    id: `INC-${Date.now()}`,
    atm_id: atm.atm_id,
    location: atm.location,
    type,
    severity,
    timestamp: new Date(),
    description: `${type} detected at ${atm.location}`,
    status: severity === 'high' ? 'escalated' : 'open',
    exposure: Math.floor(Math.random() * 100000),
    complaints: Math.floor(Math.random() * 30),
    downtime: Math.round(Math.random() * 60 * 10) / 10
  };
}

export function generateSimulationLog(): { 
  type: 'incident' | 'prediction' | 'automation' | 'alert'; 
  message: string;
  severity: 'info' | 'warning' | 'error' | 'success';
  atm_id?: string;
} {
  const types = ['incident', 'prediction', 'automation', 'alert'] as const;
  const type = types[Math.floor(Math.random() * types.length)];
  const atm = mockATMs[Math.floor(Math.random() * mockATMs.length)];
  
  const messages = {
    incident: [
      `New incident detected at ${atm.location}`,
      `Card reader malfunction reported: ${atm.atm_id}`,
      `High transaction volume alert: ${atm.atm_id}`
    ],
    prediction: [
      `Risk score updated for ${atm.atm_id}: ${(Math.random() * 0.5 + 0.3).toFixed(2)}`,
      `Predicted failure probability: ${(Math.random() * 100).toFixed(1)}%`,
      `Model confidence level: ${(Math.random() * 0.3 + 0.7).toFixed(2)}`
    ],
    automation: [
      `Auto-escalation triggered for ${atm.atm_id}`,
      `Maintenance ticket created: ${atm.location}`,
      `Cash replenishment scheduled: ${atm.atm_id}`
    ],
    alert: [
      `System health check completed`,
      `Network connectivity restored: ${atm.location}`,
      `Security scan completed for fleet`
    ]
  };
  
  const severities = {
    incident: 'warning' as const,
    prediction: 'info' as const,
    automation: 'success' as const,
    alert: 'info' as const
  };
  
  const messageList = messages[type];
  return {
    type,
    message: messageList[Math.floor(Math.random() * messageList.length)],
    severity: severities[type],
    atm_id: atm.atm_id
  };
}
