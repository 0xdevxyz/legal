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
  website?: string;        // Honeypot – bleibt bei Menschen leer
  source?: string;
  form_ts?: number;        // Alt-Feld, vom Server nicht mehr ausgewertet
  form_token?: string;     // vom Server ausgestellt und signiert
  turnstile_token?: string;

  // Herkunft. Ohne diese Felder laesst sich nicht sagen, welche Anzeige einen
  // Lead gebracht hat — bei bezahltem Traffic ist das die zentrale Frage.
  campaign?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  utm_content?: string;
  utm_term?: string;
  landing_path?: string;
}

export interface WaitlistJoinResponse {
  status: 'pending_confirmation' | 'already_registered';
  message: string;
}

export interface WaitlistPlaetze {
  gesamt: number;
  vergeben: number;
  frei: number;
}
