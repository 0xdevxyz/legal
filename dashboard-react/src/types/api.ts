export interface ComplianceAnalysis {
  url: string;
  compliance_score: number;
  timestamp: string;
  findings: {
    [key: string]: Finding;
  };
  summary: {
    critical_issues: number;
    warnings: number;
    passed: number;
    total_abmahn_risiko: string;
  };
  ai_fixes_available: boolean;
  expert_consultation_recommended: boolean;
}

export interface Finding {
  category?: string;
  status: 'error' | 'warning' | 'success';
  severity: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  description?: string;
  details?: string;
  abmahn_risiko_euro?: string;
  fix_available: boolean;
  estimated_risk?: {
    abmahn_risiko_euro: string;
  };
}

export interface LegalNews {
  id: string;
  type: 'critical' | 'info' | 'tip';
  title: string;
  description: string;
  timestamp: string;
  action_available: boolean;
  action_text?: string;
}

export interface ComplianceTrend {
  date: string;
  score: number;
}

export interface ApiResponse<T> {
  data: T;
  status: 'success' | 'error';
  message?: string;
}
