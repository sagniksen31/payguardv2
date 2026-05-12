"use client";

import { useAppContext } from "@/lib/app-context"
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis,  
  Tooltip, 
  CartesianGrid,
  BarChart,
  Bar,
  ComposedChart,
  Legend
} from 'recharts';


export function IssueDistributionChart() {
  const { incidents } = useAppContext()

  if (!incidents?.length) return <div>Loading...</div>

  const palette = ["#ef4444", "#f59e0b", "#22c55e", "#3b82f6", "#8b5cf6", "#d4a84b"];
  const grouped = incidents.reduce<Record<string, number>>((acc, item) => {
    const key = String(item.type || "unknown");
    acc[key] = (acc[key] || 0) + Number(item.count || 0);
    return acc;
  }, {});

  const total = Object.values(grouped).reduce((sum, value) => sum + value, 0) || 1;
  const data = Object.entries(grouped).map(([label, value], index) => ({
    label: String(label).replace(/_/g, " "),
    value,
    percent: Math.round((value / total) * 100),
    color: palette[index % palette.length],
  }))

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-foreground">Issue Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="w-40 h-40">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={45}
                  outerRadius={70}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex-1 space-y-2">
            {data.map((item, index) => (
              <div key={`${item.label}-${index}`} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div 
                    className="w-3 h-3 rounded-full" 
                    style={{ backgroundColor: item.color }} 
                  />
                  <span className="text-muted-foreground">{item.label}</span>
                </div>
                <span className="font-mono" style={{ color: item.color }}>{item.percent}%</span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export function DailyRiskTrendChart() {
  const { dailyRiskTrend } = useAppContext()
  if (!dailyRiskTrend.length) return <div>Loading...</div>

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-foreground">Daily Risk Score Trend</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4 mb-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-0.5 bg-danger" />
            <span className="text-xs text-muted-foreground">Avg Risk</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded bg-gold" />
            <span className="text-xs text-muted-foreground">HIGH Count</span>
          </div>
        </div>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={dailyRiskTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
              <XAxis 
                dataKey="date" 
                tick={{ fill: '#737373', fontSize: 10 }} 
                axisLine={{ stroke: '#262626' }}
                tickLine={false}
              />
              <YAxis 
                yAxisId="left"
                tick={{ fill: '#737373', fontSize: 10 }} 
                axisLine={{ stroke: '#262626' }}
                tickLine={false}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                tick={{ fill: '#737373', fontSize: 10 }} 
                axisLine={{ stroke: '#262626' }}
                tickLine={false}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#111111', 
                  border: '1px solid #262626',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#f5f5f5' }}
              />
              <Line 
                yAxisId="left"
                type="monotone" 
                dataKey="avgRisk" 
                stroke="#ef4444" 
                strokeWidth={2}
                dot={{ fill: '#ef4444', strokeWidth: 0, r: 4 }}
              />
              <Bar 
                yAxisId="right"
                dataKey="highCount" 
                fill="#d4a84b" 
                radius={[4, 4, 0, 0]}
                maxBarSize={30}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}

export function AvailabilityChart() {
  const { analysisData, fleetMetrics } = useAppContext()

  if (!analysisData || !fleetMetrics) return <div>Loading...</div>

  const data = [
    {
      strategy: "Reactive",
      value: Math.round(Number(analysisData.availability.fleet_availability_reactive ?? 0) * 100),
      color: "#737373",
    },
    {
      strategy: "Automated",
      value: Math.round(Number(analysisData.availability.fleet_availability_automated ?? 0) * 100),
      color: "#d4a84b",
    },
    {
      strategy: "Proactive",
      value: Math.round(fleetMetrics.fleetAvailabilityProactive * 100),
      color: "#22c55e",
    },
  ]
  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-foreground">Availability by Strategy</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {data.map((item) => (
            <div key={item.strategy} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">{item.strategy}</span>
                <span className="font-mono" style={{ color: item.color }}>{item.value}%</span>
              </div>
              <div className="h-4 bg-secondary rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full transition-all duration-500"
                  style={{ 
                    width: `${item.value}%`,
                    backgroundColor: item.color
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
