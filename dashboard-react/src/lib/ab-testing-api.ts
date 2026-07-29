/**
 * A/B-Testing für das Cookie-Banner
 *
 * Gegenstelle: backend/ab_test_routes.py (Prefix /api/ab-tests).
 * Alle Verwaltungsrouten verlangen einen Token und prüfen serverseitig, ob die
 * site_id zum Konto gehört — der Client muss das nicht zusätzlich absichern.
 * Die Typen bilden die Antworten des Backends 1:1 ab.
 */

import { getApiClient } from '@/lib/api-client';

const client = getApiClient();

export type ABTestStatus = 'draft' | 'running' | 'paused' | 'completed';
export type ABVariant = 'A' | 'B';

/** Teilmenge der Banner-Config, die sich sinnvoll gegeneinander testen lässt. */
export interface ABVariantConfig {
  layout?: string;
  primary_color?: string;
  accent_color?: string;
  button_style?: string;
  position?: string;
  texts?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface ABTestListItem {
  id: number;
  name: string;
  status: ABTestStatus;
  traffic_split: number;
  start_date: string | null;
  end_date: string | null;
  winner: ABVariant | null;
  total_impressions: number;
  created_at: string;
}

export interface ABTestMeta {
  id: number;
  site_id: string;
  name: string;
  description: string | null;
  hypothesis: string | null;
  variant_a_config: ABVariantConfig;
  variant_b_config: ABVariantConfig;
  traffic_split: number;
  status: ABTestStatus;
  winner: ABVariant | null;
  start_date: string | null;
  end_date: string | null;
  min_sample_size: number;
  confidence_level: number;
  created_at: string;
  updated_at: string;
}

/** Aggregat je Variante. `rate` ist die Zustimmungsquote in Prozent. */
export interface ABVariantResult {
  impressions: number;
  accepted_all: number;
  accepted_partial?: number;
  rejected_all?: number;
  accepted_analytics?: number;
  accepted_marketing?: number;
  accepted_functional?: number;
  avg_decision_time?: number;
  rate: number;
}

export interface ABTestDetail {
  success: boolean;
  test: ABTestMeta;
  results: {
    variant_a: ABVariantResult;
    variant_b: ABVariantResult;
    improvement_percent: number;
    leading_variant: string | null;
  };
  statistics: {
    z_score: number;
    p_value: number;
    is_significant: boolean;
    sample_reached: boolean;
    confidence_level: number;
  };
}

export interface ABTestCreateInput {
  site_id: string;
  name: string;
  description?: string;
  hypothesis?: string;
  variant_a_config: ABVariantConfig;
  variant_b_config: ABVariantConfig;
  traffic_split?: number;
  min_sample_size?: number;
  confidence_level?: number;
}

export async function listSiteTests(
  siteId: string,
  status?: ABTestStatus
): Promise<ABTestListItem[]> {
  const res = await client.get(`/api/ab-tests/site/${encodeURIComponent(siteId)}`, {
    params: status ? { status } : undefined,
  });
  return res.data?.tests ?? [];
}

export async function getTest(testId: number): Promise<ABTestDetail> {
  const res = await client.get(`/api/ab-tests/${testId}`);
  return res.data;
}

export async function createTest(
  input: ABTestCreateInput
): Promise<{ test_id: number; status: ABTestStatus }> {
  const res = await client.post('/api/ab-tests', input);
  return res.data;
}

export async function startTest(testId: number) {
  const res = await client.post(`/api/ab-tests/${testId}/start`);
  return res.data;
}

/** Ohne `winner` wird der Test ohne Sieger beendet. */
export async function stopTest(testId: number, winner?: ABVariant) {
  const res = await client.post(`/api/ab-tests/${testId}/stop`, null, {
    params: winner ? { winner } : undefined,
  });
  return res.data;
}

export async function deleteTest(testId: number) {
  const res = await client.delete(`/api/ab-tests/${testId}`);
  return res.data;
}
