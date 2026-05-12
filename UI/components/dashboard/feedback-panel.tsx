"use client";

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Badge } from '@/components/ui/badge';
import { 
  CheckCircle, 
  MessageSquare, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus,
  Activity,
  Send
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAppContext } from '@/lib/app-context';

const issueTypes = [
  'Card Declined',
  'Auth Timeout', 
  'Network Failure',
  'Cash Dispense Error',
  'Hardware Fault',
  'Security Alert',
  'Cash Low',
  'Receipt Printer Error'
];

const actualIssueOptions = [
  'Card Reader Malfunction',
  'Network Connectivity Issue',
  'Software Bug',
  'Hardware Component Failure',
  'Cash Jam',
  'Power Fluctuation',
  'Environmental Factor',
  'User Error',
  'No Issue Found',
  'Other'
];

export function FeedbackPanel() {
  const { atms } = useAppContext();
  const [submitted, setSubmitted] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedATM, setSelectedATM] = useState<string>('');
  
  // Incident Context (auto-populated based on ATM selection)
  const [incidentContext, setIncidentContext] = useState({
    issueType: '',
    riskScore: 0,
    escalationProbability: 0,
    driftSignal: 'stable' as 'stable' | 'increasing' | 'decreasing'
  });
  
  // Technician Input
  const [technicianInput, setTechnicianInput] = useState({
    actualIssue: '',
    predictionAccuracy: '' as '' | 'correct' | 'over-predicted' | 'under-predicted',
    actualResolutionTime: '',
    notes: ''
  });

  // Update incident context when ATM is selected
  useEffect(() => {
    if (selectedATM) {
      const atm = atms.find(a => a.atm_id === selectedATM);
      if (atm) {
        const riskScore = atm.riskScore ?? atm.risk_score ?? 0;
        setIncidentContext({
          issueType: atm.issue_type || 'Unknown',
          riskScore,
          escalationProbability: atm.escalation_probability ?? Math.min(1, riskScore / 100),
          driftSignal: riskScore > 65 ? 'increasing' : 'stable'
        });
      }
    }
  }, [selectedATM, atms]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError('');
    setSuccessMessage('');
    setIsSubmitting(true);
    try {
      const actionHelpful =
        technicianInput.predictionAccuracy === 'correct'
          ? 'yes'
          : technicianInput.predictionAccuracy === 'over-predicted'
            ? 'partial'
            : 'no';

      const response = await fetch('http://localhost:8000/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          atm_id: selectedATM,
          predicted_issue: incidentContext.issueType || 'UNKNOWN',
          actual_issue: technicianInput.actualIssue,
          action_helpful: actionHelpful,
          notes: technicianInput.notes,
          resolution_time_minutes: Number(technicianInput.actualResolutionTime) || 0,
        }),
      });

      if (!response.ok) {
        throw new Error(`Feedback API failed with status ${response.status}`);
      }

      setSubmitted(true);
      setSuccessMessage('Feedback submitted successfully');
      setSelectedATM('');
      setTechnicianInput({
        actualIssue: '',
        predictionAccuracy: '',
        actualResolutionTime: '',
        notes: ''
      });
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Failed to submit feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  const DriftIcon = incidentContext.driftSignal === 'increasing' 
    ? TrendingUp 
    : incidentContext.driftSignal === 'decreasing' 
    ? TrendingDown 
    : Minus;

  const driftColor = incidentContext.driftSignal === 'increasing'
    ? 'text-danger'
    : incidentContext.driftSignal === 'decreasing'
    ? 'text-success'
    : 'text-muted-foreground';

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-foreground flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-gold" />
          Model Feedback - Structured Input
        </CardTitle>
        <CardDescription>
          Help improve predictions by providing detailed feedback on model accuracy and actual outcomes
        </CardDescription>
      </CardHeader>
      <CardContent>
        {submitted ? (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mb-4">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Feedback Submitted Successfully</h3>
            <p className="text-muted-foreground">{successMessage || 'Thank you for helping improve our prediction model!'}</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* LEFT: Incident Context */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-border">
                  <Activity className="h-4 w-4 text-gold" />
                  <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">Incident Context</h3>
                </div>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="atmId">ATM ID</Label>
                    <Select 
                      value={selectedATM}
                      onValueChange={setSelectedATM}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select ATM" />
                      </SelectTrigger>
                      <SelectContent>
                        {atms.map(atm => (
                          <SelectItem key={atm.atm_id} value={atm.atm_id}>
                            {atm.atm_id} - {atm.location}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {selectedATM && (
                    <>
                      <div className="p-4 bg-secondary/30 rounded-lg space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Issue Type</span>
                          <Badge variant="outline" className="border-gold/50 text-gold">
                            {incidentContext.issueType}
                          </Badge>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Risk Score</span>
                          <span className={cn(
                            "text-sm font-mono",
                            incidentContext.riskScore >= 0.7 ? "text-danger" : 
                            incidentContext.riskScore >= 0.4 ? "text-warning" : "text-success"
                          )}>
                            {incidentContext.riskScore.toFixed(2)}
                          </span>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Escalation Probability</span>
                          <span className={cn(
                            "text-sm font-mono",
                            incidentContext.escalationProbability >= 0.7 ? "text-danger" : "text-warning"
                          )}>
                            {(incidentContext.escalationProbability * 100).toFixed(0)}%
                          </span>
                        </div>
                        
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground">Drift Signal</span>
                          <div className="flex items-center gap-1">
                            <DriftIcon className={cn("h-4 w-4", driftColor)} />
                            <span className={cn("text-sm capitalize", driftColor)}>
                              {incidentContext.driftSignal}
                            </span>
                          </div>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* RIGHT: Technician Input */}
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-border">
                  <AlertTriangle className="h-4 w-4 text-gold" />
                  <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">Technician Input</h3>
                </div>
                
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="actualIssue">Actual Issue</Label>
                    <Select
                      value={technicianInput.actualIssue}
                      onValueChange={(value) => setTechnicianInput(prev => ({ ...prev, actualIssue: value }))}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select actual issue found" />
                      </SelectTrigger>
                      <SelectContent>
                        {actualIssueOptions.map(issue => (
                          <SelectItem key={issue} value={issue}>{issue}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Prediction Accuracy</Label>
                    <RadioGroup
                      value={technicianInput.predictionAccuracy}
                      onValueChange={(value) => setTechnicianInput(prev => ({ 
                        ...prev, 
                        predictionAccuracy: value as 'correct' | 'over-predicted' | 'under-predicted'
                      }))}
                      className="flex flex-col space-y-2"
                    >
                      <div className="flex items-center space-x-2 p-2 rounded-lg hover:bg-secondary/30 transition-colors">
                        <RadioGroupItem value="correct" id="correct" />
                        <Label htmlFor="correct" className="flex items-center gap-2 cursor-pointer">
                          <CheckCircle className="h-4 w-4 text-success" />
                          <span>Correct - Prediction matched actual outcome</span>
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2 p-2 rounded-lg hover:bg-secondary/30 transition-colors">
                        <RadioGroupItem value="over-predicted" id="over-predicted" />
                        <Label htmlFor="over-predicted" className="flex items-center gap-2 cursor-pointer">
                          <TrendingUp className="h-4 w-4 text-warning" />
                          <span>Over-predicted - Risk was lower than predicted</span>
                        </Label>
                      </div>
                      <div className="flex items-center space-x-2 p-2 rounded-lg hover:bg-secondary/30 transition-colors">
                        <RadioGroupItem value="under-predicted" id="under-predicted" />
                        <Label htmlFor="under-predicted" className="flex items-center gap-2 cursor-pointer">
                          <TrendingDown className="h-4 w-4 text-danger" />
                          <span>Under-predicted - Risk was higher than predicted</span>
                        </Label>
                      </div>
                    </RadioGroup>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="resolutionTime">Actual Resolution Time (minutes)</Label>
                    <Input
                      id="resolutionTime"
                      type="number"
                      placeholder="Enter resolution time in minutes"
                      value={technicianInput.actualResolutionTime}
                      onChange={(e) => setTechnicianInput(prev => ({ ...prev, actualResolutionTime: e.target.value }))}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="notes">Notes</Label>
                    <Textarea
                      id="notes"
                      placeholder="Provide any additional context, observations, or recommendations..."
                      value={technicianInput.notes}
                      onChange={(e) => setTechnicianInput(prev => ({ ...prev, notes: e.target.value }))}
                      rows={4}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <div className="mt-6 pt-4 border-t border-border">
              {submitError && (
                <p className="text-sm text-danger mb-3 text-center">{submitError}</p>
              )}
              <Button 
                type="submit" 
                className="w-full bg-gold hover:bg-[#e8c675] text-background font-semibold"
                disabled={!selectedATM || !technicianInput.actualIssue || !technicianInput.predictionAccuracy || isSubmitting}
              >
                <Send className="h-4 w-4 mr-2" />
                {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
              </Button>
              <p className="text-xs text-muted-foreground text-center mt-2">
                Your feedback helps train and improve our prediction models
              </p>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
