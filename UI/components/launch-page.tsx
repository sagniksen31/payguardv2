"use client";

import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAppContext } from '@/lib/app-context';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Slider } from '@/components/ui/slider';
import { 
  Database, 
  Radio, 
  Upload, 
  Play, 
  Loader2, 
  CheckCircle2, 
  AlertTriangle,
  FileSpreadsheet,
  X
} from 'lucide-react';
import type { SystemMode } from '@/lib/types';

const modeOptions: { value: SystemMode; label: string; description: string; icon: React.ReactNode }[] = [
  {
    value: 'stable',
    label: 'Stable Mode',
    description: 'Run simulation with optional deterministic or randomized execution',
    icon: <Database className="h-5 w-5" />
  },
  {
    value: 'live',
    label: 'Live ATM Network',
    description: 'Live ATM Network — real-time streaming predictions',
    icon: <Radio className="h-5 w-5" />
  },
  {
    value: 'csv',
    label: 'CSV Upload',
    description: 'Analyze your own ATM data from CSV file',
    icon: <Upload className="h-5 w-5" />
  }
];

export function LaunchPage() {
  const router = useRouter();
  const { 
    systemMode, 
    setSystemMode, 
    config, 
    updateConfig, 
    runAnalysis, 
    isLoading,
    loadingStep,
    csvData,
    csvErrors,
    uploadCSV,
    clearCSVData
  } = useAppContext();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [deterministic, setDeterministic] = useState(true);

  const handleFileUpload = async (file: File) => {
    if (file && file.type === 'text/csv') {
      await uploadCSV(file);
    }
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    await handleFileUpload(file);
  };

  const handleSubmit = () => {
    if (systemMode === 'live') {
      router.push('/live-network');
      return;
    }

    runAnalysis({
      mode: systemMode,
      deterministic,
      config
    });
  };

  const getButtonText = () => {
    if (isLoading) return loadingStep || 'Processing...';
    switch (systemMode) {
      case 'stable': return 'Run Analysis';
      case 'live': return 'Start Simulation';
      case 'csv': return 'Analyze Uploaded Data';
    }
  };

  const isSubmitDisabled = isLoading || (systemMode === 'csv' && !csvData);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-gold font-bold text-xl">PayGuard</span>
            <span className="text-danger font-medium text-xl">INTELLIGENCE</span>
          </div>
          <span className="text-muted-foreground text-sm">PREDICTIVE ATM INCIDENT INTELLIGENCE PLATFORM</span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 lg:p-10">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Title Section */}
          <div className="text-center space-y-2">
            <h1 className="text-3xl font-bold text-foreground">System Configuration</h1>
            <p className="text-muted-foreground">
              Configure your analysis parameters and data source to begin
            </p>
          </div>

          {/* Mode Selection */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-gold">Select Data Mode</CardTitle>
              <CardDescription>Choose how you want to run the analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {modeOptions.map((option) => (
                  <button
                    key={option.value}
                    onClick={() => setSystemMode(option.value)}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      systemMode === option.value
                        ? 'border-gold bg-gold/10'
                        : 'border-border hover:border-muted-foreground/50'
                    }`}
                  >
                    <div className={`mb-3 ${systemMode === option.value ? 'text-gold' : 'text-muted-foreground'}`}>
                      {option.icon}
                    </div>
                    <h3 className={`font-semibold mb-1 ${systemMode === option.value ? 'text-gold' : 'text-foreground'}`}>
                      {option.label}
                    </h3>
                    <p className="text-sm text-muted-foreground">{option.description}</p>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
          {/* Stable Mode Toggle */}
          {systemMode === 'stable' && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-gold">Execution Mode</CardTitle>
                <CardDescription>
                  Toggle between reproducible and randomized simulation
                </CardDescription>
              </CardHeader>
              <CardContent className="flex items-center justify-between">
                <span className="text-muted-foreground">Randomized</span>

                <Switch
                  checked={deterministic}
                  onCheckedChange={setDeterministic}
                />

                <span className="text-gold font-medium">Deterministic</span>
              </CardContent>
            </Card>
          )}

          {/* CSV Upload Section */}
          {systemMode === 'csv' && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-gold">Upload CSV File</CardTitle>
                <CardDescription>
                  Required columns: atm_id, location, transaction_volume, avg_amount, downtime_minutes, complaint_count, error_code
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={handleDrop}
                  className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                    dragActive ? 'border-gold bg-gold/5' : 'border-border'
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
                    className="hidden"
                  />
                  <FileSpreadsheet className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-foreground mb-2">
                    Drag and drop your CSV file here, or{' '}
                    <button 
                      onClick={() => fileInputRef.current?.click()}
                      className="text-gold hover:underline"
                    >
                      browse
                    </button>
                  </p>
                  <p className="text-sm text-muted-foreground">Maximum file size: 10MB</p>
                </div>

                {/* CSV Errors */}
                {csvErrors.length > 0 && (
                  <div className="mt-4 p-4 rounded-lg bg-danger/10 border border-danger/20">
                    <div className="flex items-center gap-2 text-danger mb-2">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="font-medium">Validation Errors</span>
                    </div>
                    <ul className="text-sm text-danger/80 list-disc list-inside">
                      {csvErrors.map((error, i) => (
                        <li key={i}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* CSV Preview */}
                {csvData && csvData.length > 0 && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 text-success">
                        <CheckCircle2 className="h-4 w-4" />
                        <span className="font-medium">{csvData.length} rows loaded successfully</span>
                      </div>
                      <Button variant="ghost" size="sm" onClick={clearCSVData}>
                        <X className="h-4 w-4 mr-1" />
                        Clear
                      </Button>
                    </div>
                    <div className="overflow-x-auto border border-border rounded-lg">
                      <table className="w-full text-sm">
                        <thead className="bg-secondary">
                          <tr>
                            <th className="px-3 py-2 text-left text-foreground">ATM ID</th>
                            <th className="px-3 py-2 text-left text-foreground">Location</th>
                            <th className="px-3 py-2 text-left text-foreground">Volume</th>
                            <th className="px-3 py-2 text-left text-foreground">Avg Amount</th>
                            <th className="px-3 py-2 text-left text-foreground">Downtime</th>
                          </tr>
                        </thead>
                        <tbody>
                          {csvData.slice(0, 5).map((row, i) => (
                            <tr key={i} className="border-t border-border">
                              <td className="px-3 py-2 text-muted-foreground">{row.atm_id}</td>
                              <td className="px-3 py-2 text-muted-foreground">{row.location}</td>
                              <td className="px-3 py-2 text-muted-foreground">{row.transaction_volume}</td>
                              <td className="px-3 py-2 text-muted-foreground">{row.avg_amount}</td>
                              <td className="px-3 py-2 text-muted-foreground">{row.downtime_minutes}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Configuration Options */}
          {systemMode !== 'live' && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-gold">Configuration</CardTitle>
                <CardDescription>Adjust analysis parameters</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Number of Days */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="days" className="text-foreground">Number of Days</Label>
                    <span className="text-gold font-mono">{config.numberOfDays}</span>
                  </div>
                  <Slider
                    id="days"
                    value={[config.numberOfDays]}
                    onValueChange={([value]) => updateConfig({ numberOfDays: value })}
                    min={7}
                    max={365}
                    step={1}
                    className="w-full"
                  />
                  <p className="text-sm text-muted-foreground">Historical data range for analysis</p>
                </div>

                {/* Incidents per ATM */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="incidents" className="text-foreground">Max Incidents per ATM</Label>
                    <span className="text-gold font-mono">{config.incidentsPerATM}</span>
                  </div>
                  <Slider
                    id="incidents"
                    value={[config.incidentsPerATM]}
                    onValueChange={([value]) => updateConfig({ incidentsPerATM: value })}
                    min={1}
                    max={50}
                    step={1}
                    className="w-full"
                  />
                  <p className="text-sm text-muted-foreground">Maximum incidents to analyze per ATM</p>
                </div>

                {/* Force Retrain */}
                <div className="flex items-center justify-between py-2">
                  <div>
                    <Label htmlFor="retrain" className="text-foreground">Force Model Retrain</Label>
                    <p className="text-sm text-muted-foreground">Retrain ML model with latest data</p>
                  </div>
                  <Switch
                    id="retrain"
                    checked={config.forceRetrain}
                    onCheckedChange={(checked) => updateConfig({ forceRetrain: checked })}
                  />
                </div>
              </CardContent>
            </Card> 
          )}
          {/* Submit Button */}
          <Button
            onClick={handleSubmit}
            disabled={isSubmitDisabled}
            className="w-full h-14 text-lg font-semibold bg-gold hover:bg-gold-light text-background"
          >
            {isLoading ? (
              <>
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                {loadingStep}
              </>
            ) : (
              <>
                <Play className="mr-2 h-5 w-5" />
                {getButtonText()}
              </>
            )}
          </Button>

          {/* Loading Progress */}
          {isLoading && (
            <div className="space-y-2">
              <div className="h-2 bg-secondary rounded-full overflow-hidden">
                <div className="h-full bg-gold animate-pulse" style={{ width: '60%' }} />
              </div>
              <p className="text-sm text-center text-muted-foreground">{loadingStep}</p>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border px-6 py-4">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>PayGuard Intelligence Platform v2.2</span>
          <span>Powered by Predictive Analytics</span>
        </div>
      </footer>
    </div>
  );
}
