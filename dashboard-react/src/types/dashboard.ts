import { ComplianceAnalysis, LegalNews, ComplianceTrend } from './api';

export interface DashboardMetrics {
  totalScore: number;
  websites: number;
  criticalIssues: number;
  scansAvailable: number;
  scansUsed: number;
}

export interface Website {
  id: string;
  url: string;
  name: string;
  lastScan: string;
  complianceScore: number;
  status: 'active' | 'scanning' | 'error' | 'completed';
}

export interface User {
  id: string;
  email: string;
  name: string;
  plan: 'ki' | 'expert';
  subscriptionStatus: 'active' | 'inactive' | 'cancelled';
}

export interface DashboardState {
  currentWebsite: Website | null;
  metrics: DashboardMetrics;
  analysisData: ComplianceAnalysis | null;
  legalNews: LegalNews[];
  complianceTrends: ComplianceTrend[];
  isLoading: boolean;
  error: string | null;
}
