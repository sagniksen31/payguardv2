"use client";

import { useMemo, useRef, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

const CONFIGURED_API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");
const DEFAULT_API_BASE_URL = "http://localhost:8000";

function buildApiCandidates(path: string): string[] {
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  const candidates = [
    CONFIGURED_API_BASE_URL ? `${CONFIGURED_API_BASE_URL}${cleanPath}` : "",
    `${DEFAULT_API_BASE_URL}${cleanPath}`,
    cleanPath,
  ].filter(Boolean);

  return [...new Set(candidates)];
}

async function fetchFromApi(path: string, init?: RequestInit): Promise<Response> {
  const candidates = buildApiCandidates(path);
  let lastError: unknown;

  for (const url of candidates) {
    try {
      const res = await fetch(url, init);
      if (res.ok) return res;
      lastError = new Error(`${url} -> ${res.status}`);
    } catch (error) {
      lastError = error;
    }
  }

  throw new Error(`All API targets failed for ${path}: ${String(lastError)}`);
}

type StreamLog = {
  atm_id: string;
  location: string;
  issue_type: string;
  transaction_volume: number;
  avg_amount: number;
  downtime_minutes: number;
  complaint_count: number;
  error_code?: string;
  drift_signal?: number;
};

type LivePrediction = {
  atm_id: string;
  risk_score: number;
  risk_label: "LOW" | "MEDIUM" | "HIGH";
  issue_type: string;
  escalation_probability: number;
  downtime_minutes: number;
  drift_signal: number;
  failure_pressure: number;
};

async function fetchBatch(): Promise<StreamLog[]> {
  const res = await fetchFromApi("/live-batch");
  const payload = await res.json();
  return Array.isArray(payload) ? (payload as StreamLog[]) : [];
}

export default function LiveNetworkPage() {
  const [liveData, setLiveData] = useState<LivePrediction[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [processingAtm, setProcessingAtm] = useState<string>("");
  const [lastEvent, setLastEvent] = useState<LivePrediction | null>(null);
  const [metrics, setMetrics] = useState({
    total: 0,
    high: 0,
    medium: 0,
    low: 0,
    avgScore: 0,
    activeAtms: 0,
  });

  const isRunningRef = useRef(false);
  const allEventsRef = useRef<LivePrediction[]>([]);

  const topIssue = useMemo(() => {
    if (!liveData.length) return "N/A";
    const counts = liveData.reduce<Record<string, number>>((acc, row) => {
      acc[row.issue_type] = (acc[row.issue_type] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "N/A";
  }, [liveData]);
  const avgDowntime = useMemo(() => {
    if (!liveData.length) return 0;
    return liveData.reduce((acc, row) => acc + row.downtime_minutes, 0) / liveData.length;
  }, [liveData]);

  function updateState(batchPreds: LivePrediction[]) {
    allEventsRef.current = [...batchPreds, ...allEventsRef.current].slice(0, 50);
    setLiveData(allEventsRef.current);
    setLastEvent(batchPreds[0] ?? null);

    const high = allEventsRef.current.filter((x) => x.risk_label === "HIGH").length;
    const medium = allEventsRef.current.filter((x) => x.risk_label === "MEDIUM").length;
    const low = allEventsRef.current.filter((x) => x.risk_label === "LOW").length;
    const avgScore = allEventsRef.current.length
      ? allEventsRef.current.reduce((acc, row) => acc + row.risk_score, 0) / allEventsRef.current.length
      : 0;
    const activeAtms = new Set(allEventsRef.current.map((x) => x.atm_id)).size;

    setMetrics((prev) => ({
      total: prev.total + batchPreds.length,
      high,
      medium,
      low,
      avgScore,
      activeAtms,
    }));
  }

  async function runSimulation() {
    isRunningRef.current = true;
    setIsStreaming(true);

    while (isRunningRef.current) {
      try {
        const batch = await fetchBatch();
        const batchPredictions: LivePrediction[] = [];

        for (const log of batch) {
          if (!isRunningRef.current) break;
          setProcessingAtm(log.atm_id);

          try {
            const res = await fetchFromApi("/predict", {
              method: "POST",
              body: JSON.stringify(log),
              headers: { "Content-Type": "application/json" },
            });

            const pred = await res.json().catch(() => ({
              ...log,
              risk_score: 50,
              risk_label: "MEDIUM",
              issue_type: log.issue_type ?? "UNKNOWN",
            }));

            batchPredictions.push({
              atm_id: String(pred.atm_id ?? log.atm_id),
              risk_label: (pred.risk_label ?? "MEDIUM") as LivePrediction["risk_label"],
              risk_score: Number(pred.risk_score ?? 50),
              issue_type: String(pred.issue_type ?? log.issue_type ?? "UNKNOWN"),
              escalation_probability: Number(pred.escalation_probability ?? 0),
              downtime_minutes: Number(pred.downtime_minutes ?? log.downtime_minutes ?? 0),
              drift_signal: Number(pred.drift_signal ?? log.drift_signal ?? 0),
              failure_pressure: Number(pred.failure_pressure ?? 0),
            });
          } catch (err) {
            console.error("Live prediction failed", err);
          }
        }

        if (batchPredictions.length) {
          updateState(batchPredictions);
        }
      } catch (err) {
        console.error("Live batch failed", err);
      }

      await new Promise((r) => setTimeout(r, 2000));
    }

    setProcessingAtm("");
    setIsStreaming(false);
    isRunningRef.current = false;
  }

  function handleStart() {
    if (isRunningRef.current) return;
    runSimulation();
  }

  function handlePause() {
    isRunningRef.current = false;
    setIsStreaming(false);
    setProcessingAtm("");
  }

  function handleReset() {
    handlePause();
    setLiveData([]);
    setLastEvent(null);
    setMetrics({
      total: 0,
      high: 0,
      medium: 0,
      low: 0,
      avgScore: 0,
      activeAtms: 0,
    });
    allEventsRef.current = [];
  }

  const labelClass = (label: string) =>
    label === "HIGH" ? "text-red-500" : label === "MEDIUM" ? "text-amber-400" : "text-green-500";

  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-gold">Live ATM Network</h1>
            <p className="text-sm text-muted-foreground mt-1">
              <span className="text-green-500">{isStreaming ? "● LIVE" : "● IDLE"}</span> Real-time monitoring and scoring
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleStart} disabled={isStreaming}>Start</Button>
            <Button variant="outline" onClick={handlePause} disabled={!isStreaming}>Pause</Button>
            <Button variant="secondary" onClick={handleReset}>Reset</Button>
            <Button asChild variant="ghost"><Link href="/">Back</Link></Button>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="bg-card border-border"><CardContent className="p-4"><p className="text-xs text-muted-foreground">Total Events Processed</p><p className="text-2xl font-mono">{metrics.total}</p></CardContent></Card>
          <Card className="bg-card border-border"><CardContent className="p-4"><p className="text-xs text-muted-foreground">High Risk Count</p><p className="text-2xl font-mono text-red-500">{metrics.high}</p></CardContent></Card>
          <Card className="bg-card border-border"><CardContent className="p-4"><p className="text-xs text-muted-foreground">Average Risk Score</p><p className="text-2xl font-mono">{metrics.avgScore.toFixed(2)}</p></CardContent></Card>
          <Card className="bg-card border-border"><CardContent className="p-4"><p className="text-xs text-muted-foreground">Active ATMs</p><p className="text-2xl font-mono">{metrics.activeAtms}</p></CardContent></Card>
        </div>

        {processingAtm && (
          <p className="text-sm text-muted-foreground animate-pulse">Processing ATM... {processingAtm}</p>
        )}

        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle>Latest Decision</CardTitle>
            <CardDescription>Most recent AI risk decision</CardDescription>
          </CardHeader>
          <CardContent>
            {lastEvent ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-muted-foreground">ATM ID</p>
                    <p className="font-mono text-lg">{lastEvent.atm_id}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-semibold ${labelClass(lastEvent.risk_label)}`}>
                    {lastEvent.risk_label}
                  </span>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Issue Type</p>
                  <p className="text-foreground">{lastEvent.issue_type.replace(/_/g, " ")}</p>
                </div>
                <div className={`text-5xl font-bold ${labelClass(lastEvent.risk_label)}`}>
                  {lastEvent.risk_score.toFixed(2)}
                </div>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div><p className="text-muted-foreground">Esc. Probability</p><p>{(lastEvent.escalation_probability * 100).toFixed(1)}%</p></div>
                  <div><p className="text-muted-foreground">Downtime</p><p>{lastEvent.downtime_minutes.toFixed(1)} min</p></div>
                  <div><p className="text-muted-foreground">Drift Signal</p><p>{lastEvent.drift_signal.toFixed(1)}</p></div>
                  <div><p className="text-muted-foreground">Failure Pressure</p><p>{lastEvent.failure_pressure.toFixed(1)}</p></div>
                </div>
                <p className="text-sm text-muted-foreground">
                  {lastEvent.risk_label === "HIGH"
                    ? "Immediate intervention recommended. Escalation risk is high."
                    : lastEvent.risk_label === "MEDIUM"
                      ? "Monitor closely and prepare automated remediation."
                      : "ATM operating within normal risk boundaries."}
                </p>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No decisions yet. Start simulation to begin.</p>
            )}
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="bg-card border-border lg:col-span-2">
            <CardHeader>
              <CardTitle>Live Feed</CardTitle>
              <CardDescription>Latest 20 scored events</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-[480px] overflow-y-auto">
                {liveData.slice(0, 20).map((row, i) => (
                  <div
                    key={`${row.atm_id}-${i}`}
                    className={`p-3 border rounded flex justify-between items-center animate-in fade-in slide-in-from-top-1 ${
                      row.risk_label === "HIGH" ? "border-red-500/40 bg-red-500/5" : "border-border"
                    }`}
                  >
                    <span className="font-mono">{row.atm_id}</span>
                    <span className={labelClass(row.risk_label)}>{row.risk_label}</span>
                    <span className="font-mono">{row.risk_score.toFixed(2)}</span>
                    <span className="text-muted-foreground">{row.issue_type}</span>
                  </div>
                ))}
                {!liveData.length && <p className="text-sm text-muted-foreground">No live events yet.</p>}
              </div>
            </CardContent>
          </Card>

          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Summary Panel</CardTitle>
              <CardDescription>Current risk and issue summary</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between"><span>High</span><span className="text-red-500 font-mono">{metrics.high}</span></div>
              <div className="flex justify-between"><span>Medium</span><span className="text-amber-400 font-mono">{metrics.medium}</span></div>
              <div className="flex justify-between"><span>Low</span><span className="text-green-500 font-mono">{metrics.low}</span></div>
              <div className="flex justify-between"><span>Top Issue Type</span><span className="font-mono">{topIssue}</span></div>
              <div className="flex justify-between"><span>Avg Downtime</span><span className="font-mono">{avgDowntime.toFixed(1)} min</span></div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

