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
  status: 'error' | 'warning' | 'success';
  severity: 'critical' | 'medium' | 'low';
  title: string;
  description: string;
  abmahn_risiko_euro: string;
  fix_available: boolean;
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

export interface WaitlistJoinRequest {
  email: string;
  name?: string;
  phone?: string;
  consent: boolean;
  website?: string;
  source?: string;
}

export interface WaitlistJoinResponse {
  status: 'pending_confirmation' | 'already_registered';
  message: string;
}
