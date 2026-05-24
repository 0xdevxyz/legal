/**
 * Typed API client for Phase 10 Agency endpoints.
 * Wraps the shared apiClient (axios with JWT interceptor).
 */
import apiClient from '@/lib/api';

export interface AgencyClient {
  client_name: string;
  client_email: string | null;
  site_count: number;
  total_impressions: number;
  total_accepted: number;
  acceptance_rate: number;
}

export interface AgencyClientsResponse {
  clients: AgencyClient[];
}

export interface LogoUploadResponse {
  relative_path: string;
  filename: string;
}

/** GET /api/cookie-compliance/agency/clients */
export async function getAgencyClients(): Promise<AgencyClient[]> {
  const res = await apiClient.get<AgencyClientsResponse>(
    '/api/cookie-compliance/agency/clients',
  );
  return res.data.clients ?? [];
}

/** PATCH /api/cookie-compliance/agency/sites/{site_id}/client */
export async function assignClient(
  site_id: string,
  client_name: string | null,
  client_email: string | null,
): Promise<void> {
  await apiClient.patch(
    `/api/cookie-compliance/agency/sites/${encodeURIComponent(site_id)}/client`,
    { client_name, client_email },
  );
}

/** POST /api/cookie-compliance/agency/logo (multipart/form-data) */
export async function uploadAgencyLogo(file: File): Promise<LogoUploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await apiClient.post<LogoUploadResponse>(
    '/api/cookie-compliance/agency/logo',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return res.data;
}

/** GET /api/cookie-compliance/agency/client-report/{client_name} - triggers browser download */
export async function downloadClientReport(client_name: string): Promise<void> {
  const res = await apiClient.get(
    `/api/cookie-compliance/agency/client-report/${encodeURIComponent(client_name)}`,
    { responseType: 'blob' },
  );
  const blob = new Blob([res.data], { type: 'application/pdf' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const safe = client_name.replace(/[^a-zA-Z0-9_-]/g, '_');
  a.download = `complyo_report_${safe}.pdf`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
