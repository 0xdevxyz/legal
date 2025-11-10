/**
 * TypeScript Types for AI Compliance (ComploAI Guard)
 */

export type RiskCategory = 'prohibited' | 'high' | 'limited' | 'minimal' | 'pending';

export type AISystemStatus = 'active' | 'paused' | 'archived';

export type ScanStatus = 'pending' | 'in_progress' | 'completed' | 'failed';

export type DocumentStatus = 'draft' | 'review' | 'approved' | 'published';

export interface AISystem {
  id: string;
  name: string;
  description: string;
  vendor?: string;
  purpose: string;
  domain?: string;
  risk_category?: RiskCategory;
  risk_reasoning?: string;
  confidence_score?: number;
  compliance_score: number;
  last_assessment_date?: string;
  status: AISystemStatus;
  created_at: string;
  updated_at: string;
  website_id?: string;
  deployment_date?: string;
  data_types?: string[];
  affected_persons?: string[];
}

export interface AISystemCreate {
  name: string;
  description: string;
  vendor?: string;
  purpose: string;
  domain?: string;
  deployment_date?: string;
  data_types?: string[];
  affected_persons?: string[];
  website_id?: string;
}

export interface AISystemUpdate {
  name?: string;
  description?: string;
  vendor?: string;
  purpose?: string;
  domain?: string;
  deployment_date?: string;
  data_types?: string[];
  affected_persons?: string[];
  status?: AISystemStatus;
}

export interface ComplianceScan {
  scan_id: string;
  ai_system_id: string;
  compliance_score: number;
  overall_risk_score: number;
  risk_category: RiskCategory;
  status: ScanStatus;
  created_at: string;
  risk_assessment?: any;
  findings?: ComplianceFinding[];
  recommendations?: string;
  requirements_met?: RequirementResult[];
  requirements_failed?: RequirementResult[];
}

export interface ComplianceFinding {
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  recommendation: string;
}

export interface RequirementResult {
  requirement: string;
  article?: string;
  status?: string;
  evidence?: string;
  reason?: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
}

export interface AIDocumentation {
  id: string;
  document_type: string;
  title?: string;
  status: DocumentStatus;
  version: number;
  created_at: string;
  file_url?: string;
}

export interface RequiredDocumentation {
  type: string;
  title: string;
  description: string;
  mandatory: boolean;
}

export interface AIActRequirement {
  id: string;
  article: string;
  title: string;
  description: string;
  mandatory_for: RiskCategory[];
}

export interface RiskCategoryInfo {
  name: string;
  description: string;
  examples: string[];
  articles: string[];
}

export interface AIComplianceStats {
  total_systems: number;
  risk_distribution: Record<RiskCategory, number>;
  average_compliance_score: number;
  scans_last_30_days: number;
}

export interface Addon {
  id: string;
  addon_key: string;
  addon_name: string;
  price_monthly: number;
  status: 'active' | 'cancelled' | 'expired';
  limits: Record<string, any>;
  started_at: string;
  expires_at?: string;
  cancelled_at?: string;
}

export interface AddonCatalog {
  monthly_addons: Record<string, MonthlyAddon>;
  onetime_addons: Record<string, OnetimeAddon>;
}

export interface MonthlyAddon {
  name: string;
  tagline: string;
  price_monthly: number;
  currency: string;
  features: string[];
  limits_by_plan?: Record<string, any>;
  stripe_price_id: string;
  badge?: string;
  discount_text?: string;
  compatible_plans: string[];
}

export interface OnetimeAddon {
  name: string;
  price: number;
  currency: string;
  description: string;
  includes: string[];
  duration: string;
  stripe_price_id: string;
}

