"use client";

import { createContext, useContext, useState, useCallback, useEffect, useRef, type ReactNode } from "react";
import type {
  AnalyzeApiResponse,
  ATMData,
  DailyRiskTrend,
  FleetMetrics,
  Incident,
  RiskDistribution,
  SimulationLog,
  SystemConfig,
  SystemMode,
} from "./types";

interface AppState {
  currentPage: "launch" | "dashboard";
  systemMode: SystemMode;
  config: SystemConfig;
  isRunning: boolean;
  isLoading: boolean;
  loadingStep: string;
  lastRunTime: Date | null;
  atms: ATMData[];
  incidents: Incident[];
  dailyRiskTrend: DailyRiskTrend[];
  fleetMetrics: FleetMetrics;
  riskDistribution: RiskDistribution;
  simulationLogs: SimulationLog[];
  analysisData: AnalyzeApiResponse | null;
  csvData: ATMData[] | null;
  csvErrors: string[];
}

interface AppContextType extends AppState {
  setCurrentPage: (page: "launch" | "dashboard") => void;
  setSystemMode: (mode: SystemMode) => void;
  updateConfig: (config: Partial<SystemConfig>) => void;
  runAnalysis: (params?: {
    mode?: SystemMode;
    deterministic?: boolean;
    config?: Partial<SystemConfig>;
  }) => Promise<void>;
  startLiveSimulation: () => void;
  stopLiveSimulation: () => void;
  uploadCSV: (file: File) => Promise<void>;
  clearCSVData: () => void;
  addSimulationLog: (log: Omit<SimulationLog, 'id' | 'timestamp'>) => void;
}

const AppContext = createContext<AppContextType | null>(null);

const initialConfig: SystemConfig = {
  mode: "stable",
  numberOfDays: 60,
  incidentsPerATM: 20,
  forceRetrain: false,
};

const loadingSteps = ["Running pipeline...", "Aggregating ATM intelligence...", "Rendering dashboard..."];

function toRiskLevel(label: string | undefined): "high" | "medium" | "low" {
  if (label === "HIGH") return "high";
  if (label === "MEDIUM") return "medium";
  return "low";
}

function deriveDailyRiskTrend(raw: Array<Record<string, unknown>>): DailyRiskTrend[] {
  const grouped = new Map<string, { totalRisk: number; count: number; high: number }>();

  raw.forEach((row) => {
    const ts = String(row.timestamp ?? "");
    if (!ts) return;
    const date = ts.includes("T") ? ts.split("T")[0] : ts.slice(0, 10);
    const risk = Number(row.pre_failure_risk_score ?? 0);
    const label = String(row.risk_label ?? "LOW");

    if (!grouped.has(date)) {
      grouped.set(date, { totalRisk: 0, count: 0, high: 0 });
    }
    const acc = grouped.get(date)!;
    acc.totalRisk += risk;
    acc.count += 1;
    if (label === "HIGH") acc.high += 1;
  });

  return Array.from(grouped.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([date, acc]) => ({
      date,
      avgRisk: acc.count ? Number((acc.totalRisk / acc.count).toFixed(2)) : 0,
      highCount: acc.high,
    }));
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>({
    currentPage: "launch",
    systemMode: "stable",
    config: initialConfig,
    isRunning: false,
    isLoading: false,
    loadingStep: "",
    lastRunTime: null,
    atms: [],
    incidents: [],
    dailyRiskTrend: [],
    fleetMetrics: {
      totalIncidents: 0,
      totalEscalations: 0,
      escalationRate: 0,
      systemicClusters: 0,
      fleetAvailabilityProactive: 0,
      fleetImprovementProactivePct: 0,
      downtimePrevented: 0,
    },
    riskDistribution: {
      highRiskATMs: 0,
      mediumRiskATMs: 0,
      lowRiskATMs: 0,
      atmsNeedAction: 0,
    },
    simulationLogs: [],
    analysisData: null,
    csvData: null,
    csvErrors: [],
  });

  const simulationIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const loadingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const setCurrentPage = useCallback((page: "launch" | "dashboard") => {
    setState(prev => ({ ...prev, currentPage: page }));
  }, []);

  const setSystemMode = useCallback((mode: SystemMode) => {
    setState(prev => ({ 
      ...prev, 
      systemMode: mode,
      config: { ...prev.config, mode }
    }));
  }, []);

  const updateConfig = useCallback((config: Partial<SystemConfig>) => {
    setState(prev => ({ 
      ...prev, 
      config: { ...prev.config, ...config }
    }));
  }, []);

  const addSimulationLog = useCallback((log: Omit<SimulationLog, 'id' | 'timestamp'>) => {
    setState(prev => ({
      ...prev,
      simulationLogs: [
        {
          ...log,
          id: `log-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date()
        },
        ...prev.simulationLogs
      ].slice(0, 100) // Keep last 100 logs
    }));
  }, []);

  const runAnalysis = useCallback(async (params?: {
    mode?: SystemMode;
    deterministic?: boolean;
    config?: Partial<SystemConfig>;
  }) => {
    try {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
      }
      let step = 0;
      setState((prev) => ({ ...prev, isLoading: true, loadingStep: loadingSteps[0] }));
      loadingIntervalRef.current = setInterval(() => {
        step = (step + 1) % loadingSteps.length;
        setState((prev) => ({ ...prev, loadingStep: loadingSteps[step] }));
      }, 800);

      const effectiveMode = params?.mode ?? state.config.mode;
      const effectiveConfig = { ...state.config, ...(params?.config ?? {}) };
      const deterministic = params?.deterministic ?? true;

      const res = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          mode:
            effectiveMode === "live"
              ? "live"
              : deterministic
                ? "stable"
                : "live",
          n_days: effectiveConfig.numberOfDays,
          n_per_atm: effectiveConfig.incidentsPerATM,
          force_retrain: effectiveConfig.forceRetrain,
        }),
      });

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Analyze failed with status ${res.status}`);
      }

      const data = (await res.json()) as AnalyzeApiResponse;
      const scoredBatchSample = Array.isArray(data.scored_batch_sample) ? data.scored_batch_sample : [];
      const atms: ATMData[] = (data.per_atm_summary ?? []).map((row) => ({
        id: String(row.atm_id),
        atm_id: String(row.atm_id),
        location: String(row.location ?? "Unknown"),
        risk: String(row.risk ?? "LOW") as "HIGH" | "MEDIUM" | "LOW",
        risk_level: toRiskLevel(String(row.risk ?? "LOW")),
        riskScore: Number(row.risk_score ?? 0),
        risk_score: Number(row.risk_score ?? 0),
        downtime_minutes: Number(row.downtime_minutes ?? 0),
        complaint_count: Number(row.complaint_count ?? 0),
        transaction_volume: Number(row.transaction_volume ?? 0),
        avg_amount: Number(row.avg_amount ?? 0),
        issue_type: String(row.issue_type ?? "UNKNOWN"),
        error_code: String((row as Record<string, unknown>).error_code ?? "UNKNOWN"),
        exposure: Number(row.exposure ?? 0),
      }));
      const incidents = (data.root_cause.issue_clusters ?? []).map((cluster) => ({
        id: cluster.cluster_id,
        type: cluster.issue_type,
        count: Number(cluster.incident_count ?? 0),
        atmCount: Number(cluster.atm_count ?? 0),
        downtime: Number(cluster.total_downtime_min ?? 0),
        systemic: Boolean(cluster.is_systemic),
      }));
      const dailyRiskTrend = deriveDailyRiskTrend(scoredBatchSample);

      const escalationRate = Number(data.kpis.overall_escalation_rate ?? 0);
      const totalIncidents = Number(data.kpis.total_incidents ?? 0);
      const totalEscalations = Number(data.kpis.total_escalations ?? Math.round(totalIncidents * escalationRate));
      const fleetMetrics: FleetMetrics = {
        totalIncidents,
        totalEscalations,
        escalationRate,
        systemicClusters: incidents.filter((i) => i.systemic).length,
        fleetAvailabilityProactive: Number(data.availability.fleet_availability_proactive ?? 0),
        fleetImprovementProactivePct: Number(data.availability.fleet_improvement_proactive_pct ?? 0),
        downtimePrevented: Number(data.availability.total_downtime_prevented_proactive_min ?? 0),
      };

      const riskDistribution: RiskDistribution = {
        highRiskATMs: atms.filter((a) => a.risk === "HIGH").length,
        mediumRiskATMs: atms.filter((a) => a.risk === "MEDIUM").length,
        lowRiskATMs: atms.filter((a) => a.risk === "LOW").length,
        atmsNeedAction: atms.filter((a) => a.risk === "HIGH").length,
      };

      setState((prev): AppState => ({
        ...prev,
        isLoading: false,
        loadingStep: "",
        currentPage: "dashboard",
        lastRunTime: new Date(),
        atms,
        incidents,
        dailyRiskTrend,
        fleetMetrics,
        riskDistribution,
        analysisData: data,
      }));

      addSimulationLog({
        type: "prediction",
        message: `Analysis complete: ${atms.length} ATMs aggregated from ${scoredBatchSample.length} sampled events.`,
        severity: "success",
      });
    } catch (err) {
      console.error("API ERROR:", err);
      setState((prev) => ({ ...prev, isLoading: false, loadingStep: "" }));
      addSimulationLog({
        type: "alert",
        message: `Analysis failed: ${err instanceof Error ? err.message : "Unknown error"}`,
        severity: "error",
      });
    } finally {
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
        loadingIntervalRef.current = null;
      }
    }
  }, [state.config, addSimulationLog]);

  const startLiveSimulation = useCallback(() => {
    setState(prev => ({
      ...prev,
      isRunning: true,
      currentPage: "dashboard",
      lastRunTime: new Date(),
    }));

    addSimulationLog({
      type: "alert",
      message: "Simulation mode started. Triggering fresh analysis every 30 seconds.",
      severity: "success",
    });

    simulationIntervalRef.current = setInterval(() => {
      runAnalysis();
    }, 30000);
  }, [addSimulationLog, runAnalysis]);

  const stopLiveSimulation = useCallback(() => {
    if (simulationIntervalRef.current) {
      clearInterval(simulationIntervalRef.current);
      simulationIntervalRef.current = null;
    }
    setState(prev => ({ ...prev, isRunning: false }));
    addSimulationLog({
      type: "alert",
      message: "Live simulation stopped",
      severity: "info",
    });
  }, [addSimulationLog]);

  const uploadCSV = useCallback(async (file: File) => {
    const text = await file.text();
    const lines = text.split("\n");
    const headers = lines[0].split(",").map((h) => h.trim().toLowerCase());

    const requiredColumns = [
      "atm_id", "location", "transaction_volume", "avg_amount",
      "downtime_minutes", "complaint_count", "error_code",
    ];

    const missingColumns = requiredColumns.filter((col) => !headers.includes(col));

    if (missingColumns.length > 0) {
      setState(prev => ({
        ...prev,
        csvErrors: [`Missing required columns: ${missingColumns.join(', ')}`],
        csvData: null,
      }));
      return;
    }

    const data: ATMData[] = [];
    for (let i = 1; i < Math.min(lines.length, 100); i++) {
      const values = lines[i].split(",");
      if (values.length === headers.length) {
        const row: Record<string, string> = {};
        headers.forEach((header, index) => {
          row[header] = values[index]?.trim() || "";
        });
        data.push({
          id: String(row.atm_id),
          atm_id: String(row.atm_id),
          location: String(row.location),
          transaction_volume: Number(row.transaction_volume) || 0,
          avg_amount: Number(row.avg_amount) || 0,
          downtime_minutes: Number(row.downtime_minutes) || 0,
          complaint_count: Number(row.complaint_count) || 0,
          error_code: String(row.error_code),
          exposure: (Number(row.transaction_volume) || 0) * (Number(row.avg_amount) || 0),
        });
      }
    }

    setState(prev => ({
      ...prev,
      csvData: data,
      csvErrors: [],
      atms: data.length > 0 ? data : prev.atms,
    }));
  }, []);

  const clearCSVData = useCallback(() => {
    setState(prev => ({
      ...prev,
      csvData: null,
      csvErrors: [],
      atms: [],
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (simulationIntervalRef.current) {
        clearInterval(simulationIntervalRef.current);
      }
      if (loadingIntervalRef.current) {
        clearInterval(loadingIntervalRef.current);
      }
    };
  }, []);

  return (
    <AppContext.Provider value={{
      ...state,
      setCurrentPage,
      setSystemMode,
      updateConfig,
      runAnalysis,
      startLiveSimulation,
      stopLiveSimulation,
      uploadCSV,
      clearCSVData,
      addSimulationLog
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
}
