// Issue Location
export interface IssueLocation {
  area: string;
  hint: string;
}

// Issue Solution
export interface IssueSolution {
  code_snippet: string;
  steps: string[];
}

// New type for a single issue from the v2 endpoint
export interface ComplianceIssue {
  id: string;
  category: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  risk_euro?: number; // Keep for backward compatibility
  risk_euro_min: number;
  risk_euro_max: number;
  risk_range: string;
  recommendation?: string; // Keep for backward compatibility
  legal_basis: string;
  location: IssueLocation;
  solution: IssueSolution;
  auto_fixable: boolean;
  is_missing?: boolean;
  ai_explanation?: string;
}

// Positive Check
export interface PositiveCheck {
  category: string;
  title: string;
  status: string;
  icon: string;
}

// Issue Group structure
export interface IssueGroup {
  group_id: string;
  group_type: string;
  parent_issue?: ComplianceIssue | null;
  sub_issues: ComplianceIssue[];
  category: string;
  severity: 'critical' | 'warning' | 'info';
  solution_type: string;
  has_unified_solution: boolean;
  total_risk_euro: number;
  completed_count: number;
  total_count: number;
  title: string;
  description: string;
  icon: string;
}

// Grouping statistics
export interface GroupingStats {
  total_issues?: number;
  grouped_issues?: number;
  ungrouped_issues?: number;
  total_groups?: number;
  grouping_rate?: number;
}

// TCF (Transparency & Consent Framework) data
export interface TCFData {
  has_tcf?: boolean;
  tcf_version?: string | null;
  cmp_id?: number | null;
  cmp_name?: string | null;
  tc_string_found?: boolean;
  tc_string?: string;
  vendor_count?: number;
  detected_vendors?: Array<{
    vendor_id: string;
    vendor_name: string;
    detected_from?: string;
    requires_consent?: boolean;
    purposes?: Array<{
      id: number;
      name: string;
      legal_basis: string;
    }>;
  }>;
  issues?: ComplianceIssue[];
  error?: string;
}

// Updated type for the v2 analysis response
export interface ComplianceAnalysis {
  scan_id: string; // Added scan_id
  url: string;
  scan_timestamp: string;
  scan_duration_ms: number;
  compliance_score: number;
  total_risk_euro: number;
  critical_issues: number;
  warning_issues: number;
  total_issues: number;
  issues: ComplianceIssue[];
  positive_checks?: PositiveCheck[]; // NEW: Was funktioniert bereits
  has_accessibility_widget?: boolean; // ✅ NEU: Widget-Status vom Scanner
  recommendations: string[];
  next_steps: any[]; // Can be typed more strictly if needed
  issue_groups?: IssueGroup[]; // ✅ NEU: Gruppierte Issues
  grouping_stats?: GroupingStats; // ✅ NEU: Gruppierungs-Statistiken
  ungrouped_issues?: ComplianceIssue[]; // ✅ NEU: Einzelne, nicht gruppierte Issues
  site_id?: string; // ✅ NEU: Site-ID
  tcf_data?: TCFData; // ✅ NEU: TCF 2.2 Compliance Data
}

// The old Finding interface is no longer needed for the new endpoint
// export interface Finding { ... }

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

// Fix-Related Types
export interface FixResult {
  success: boolean;
  fix: {
    type: 'code_snippet' | 'full_document';
    format: string;
    code?: string;
    html?: string;
    pdf_url?: string;
    steps?: string[] | Array<{ step: number; title: string; description: string }>;
    legal_note?: string;
    fix_id: number;
    generated_at: string;
    ai_generated?: boolean; // Flag für KI-generierte Fixes
    placement?: string; // Wo der Code eingefügt werden soll
    test_instructions?: string[]; // Test-Anweisungen
    troubleshooting?: Array<{ problem: string; solution: string }> | string[]; // Troubleshooting-Tipps
    estimated_time?: string; // Geschätzte Zeit
    difficulty?: 'easy' | 'medium' | 'hard'; // Schwierigkeitsgrad
    cms_optimized?: string; // CMS für das der Fix optimiert wurde
    personalized?: boolean; // Personalisiert für die Website
    audit_trail?: {
      generated_at: string;
      version: string;
      user_id: number;
    };
  };
  first_fix: boolean;
  money_back_warning: boolean;
  plan_type: 'ai' | 'expert';
}

export interface UserLimits {
  success: boolean;
  limits: {
    plan_type: 'ai' | 'expert';
    websites_count: number;
    websites_max: number;
    exports_this_month: number;
    exports_max: number;
    exports_reset_date: string | null;
    fix_started: boolean;
    money_back_eligible: boolean;
    money_back_days_left: number | null;
    subscription_start: string | null;
  };
}

export interface FixHistory {
  success: boolean;
  fixes: Array<{
    id: number;
    issue_id: string;
    issue_category: string;
    fix_type: string;
    plan_type: string;
    generated_at: string;
    exported: boolean;
    exported_at: string | null;
    export_format: string | null;
  }>;
  total: number;
}
