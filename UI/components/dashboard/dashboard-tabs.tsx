"use client";

import { cn } from '@/lib/utils';
import type { DashboardTab } from '@/lib/types';
import { 
  LayoutDashboard, 
  AlertTriangle, 
  AlertCircle, 
  CheckCircle, 
  Zap, 
  Search, 
  BarChart3, 
  MessageSquare 
} from 'lucide-react';

interface DashboardTabsProps {
  activeTab: DashboardTab;
  onTabChange: (tab: DashboardTab) => void;
}

const tabs: { value: DashboardTab; label: string; icon: React.ReactNode }[] = [
  { value: 'overview', label: 'OVERVIEW', icon: <LayoutDashboard className="h-4 w-4" /> },
  { value: 'high-risk', label: 'HIGH RISK', icon: <AlertTriangle className="h-4 w-4" /> },
  { value: 'medium-risk', label: 'MEDIUM RISK', icon: <AlertCircle className="h-4 w-4" /> },
  { value: 'low-risk', label: 'LOW RISK', icon: <CheckCircle className="h-4 w-4" /> },
  { value: 'automation', label: 'AUTOMATION', icon: <Zap className="h-4 w-4" /> },
  { value: 'root-cause', label: 'ROOT CAUSE', icon: <Search className="h-4 w-4" /> },
  { value: 'availability', label: 'AVAILABILITY', icon: <BarChart3 className="h-4 w-4" /> },
  { value: 'feedback', label: 'FEEDBACK', icon: <MessageSquare className="h-4 w-4" /> },
];

export function DashboardTabs({ activeTab, onTabChange }: DashboardTabsProps) {
  return (
    <div className="border-b border-border overflow-x-auto">
      <div className="flex items-center gap-1 px-4 lg:px-6 min-w-max">
        {tabs.map((tab) => (
          <button
            key={tab.value}
            onClick={() => onTabChange(tab.value)}
            className={cn(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors border-b-2 whitespace-nowrap',
              activeTab === tab.value
                ? 'border-gold text-gold'
                : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted-foreground/30'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}
