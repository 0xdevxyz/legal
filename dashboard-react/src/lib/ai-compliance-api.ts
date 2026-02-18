/**
 * AI Compliance API Service (ComploAI Guard)
 */

import axios from 'axios';
import type {
  AISystem,
  AISystemCreate,
  AISystemUpdate,
  ComplianceScan,
  AIComplianceStats,
  Addon,
  AddonCatalog,
  RequiredDocumentation,
  AIActRequirement,
  RiskCategoryInfo
} from '@/types/ai-compliance';

// API Base URL Configuration
const getApiBaseURL = () => {
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8002';
    }
    
    if (hostname.includes('complyo.tech')) {
      return 'https://api.complyo.tech';
    }
  }
  
  return 'http://localhost:8002';
};

// Create axios instance for AI Compliance API
const aiApiClient = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 60000, // 60 seconds for AI analysis
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Request interceptor: Add auth token
aiApiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Handle errors
aiApiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message;
    console.error('AI Compliance API Error:', message);
    return Promise.reject(error);
  }
);

// ==================== AI SYSTEMS MANAGEMENT ====================

export const createAISystem = async (data: AISystemCreate): Promise<AISystem> => {
  const response = await aiApiClient.post('/api/ai/systems', data);
  return response.data;
};

export const getAISystems = async (status?: string): Promise<AISystem[]> => {
  const params = status ? { status } : {};
  const response = await aiApiClient.get('/api/ai/systems', { params });
  return response.data;
};

export const getAISystem = async (systemId: string): Promise<AISystem> => {
  const response = await aiApiClient.get(`/api/ai/systems/${systemId}`);
  return response.data;
};

export const updateAISystem = async (
  systemId: string,
  data: AISystemUpdate
): Promise<AISystem> => {
  const response = await aiApiClient.put(`/api/ai/systems/${systemId}`, data);
  return response.data;
};

export const deleteAISystem = async (systemId: string): Promise<void> => {
  await aiApiClient.delete(`/api/ai/systems/${systemId}`);
};

// ==================== COMPLIANCE SCANNING ====================

export const scanAISystem = async (
  systemId: string,
  forceRescan: boolean = false
): Promise<ComplianceScan> => {
  const response = await aiApiClient.post(`/api/ai/systems/${systemId}/scan`, {
    force_rescan: forceRescan
  });
  return response.data;
};

export const getSystemScans = async (
  systemId: string,
  limit: number = 10
): Promise<ComplianceScan[]> => {
  const response = await aiApiClient.get(`/api/ai/systems/${systemId}/scans`, {
    params: { limit }
  });
  return response.data;
};

export const getScanDetails = async (scanId: string): Promise<ComplianceScan> => {
  const response = await aiApiClient.get(`/api/ai/scans/${scanId}`);
  return response.data;
};

// ==================== AI ACT KNOWLEDGE BASE ====================

export const getAIActRequirements = async (): Promise<{
  risk_categories: Record<string, RiskCategoryInfo>;
  high_risk_requirements: AIActRequirement[];
}> => {
  const response = await aiApiClient.get('/api/ai/act/requirements');
  return response.data;
};

export const getRequirementsByCategory = async (category: string): Promise<{
  category: string;
  info: RiskCategoryInfo;
  requirements: AIActRequirement[];
  required_documentation: RequiredDocumentation[];
}> => {
  const response = await aiApiClient.get(`/api/ai/act/requirements/${category}`);
  return response.data;
};

// ==================== DOCUMENTATION ====================

export const getSystemDocumentation = async (systemId: string): Promise<{
  required: RequiredDocumentation[];
  existing: any[];
}> => {
  const response = await aiApiClient.get(`/api/ai/systems/${systemId}/documentation`);
  return response.data;
};

// ==================== STATISTICS ====================

export const getAIComplianceStats = async (): Promise<AIComplianceStats> => {
  const response = await aiApiClient.get('/api/ai/stats');
  return response.data;
};

// ==================== ADD-ON MANAGEMENT ====================

export const getAddonsCatalog = async (): Promise<AddonCatalog> => {
  const response = await aiApiClient.get('/api/addons/catalog');
  return response.data;
};

export const getMyAddons = async (): Promise<{
  addons: Addon[];
  total_monthly_cost: number;
}> => {
  const response = await aiApiClient.get('/api/addons/my-addons');
  return response.data;
};

export const subscribeToAddon = async (
  addonKey: string,
  userPlan: string = 'professional'
): Promise<{
  checkout_url: string;
  session_id: string;
}> => {
  const response = await aiApiClient.post(`/api/addons/subscribe/${addonKey}`, {
    addon_key: addonKey,
    user_plan: userPlan
  });
  return response.data;
};

export const purchaseOnetimeAddon = async (
  addonKey: string
): Promise<{
  checkout_url: string;
  session_id: string;
}> => {
  const response = await aiApiClient.post(`/api/addons/purchase/${addonKey}`);
  return response.data;
};

export const cancelAddon = async (addonKey: string): Promise<{
  message: string;
  addon_key: string;
  status: string;
}> => {
  const response = await aiApiClient.post(`/api/addons/cancel/${addonKey}`);
  return response.data;
};

// ==================== DOCUMENTATION GENERATION ====================

export type DocumentType = 'risk_assessment' | 'technical_documentation' | 'conformity_declaration';

export interface GeneratedDocument {
  id: string;
  document_type: DocumentType;
  title: string;
  status: string;
  version: string;
  created_at: string;
  updated_at?: string;
}

export const generateDocumentation = async (
  systemId: string,
  documentType: DocumentType
): Promise<{ success: boolean; document: GeneratedDocument }> => {
  const response = await aiApiClient.post(`/api/ai/systems/${systemId}/documentation/generate`, {
    document_type: documentType
  });
  return response.data;
};

export const listSystemDocuments = async (
  systemId: string
): Promise<{ documents: GeneratedDocument[] }> => {
  const response = await aiApiClient.get(`/api/ai/systems/${systemId}/documentation/list`);
  return response.data;
};

export const downloadDocumentation = async (
  docId: string,
  format: 'html' | 'pdf' = 'html'
): Promise<Blob> => {
  const response = await aiApiClient.get(`/api/ai/documentation/${docId}/download`, {
    params: { format },
    responseType: 'blob'
  });
  return response.data;
};

export const getDocumentTypeLabel = (type: DocumentType): string => {
  switch (type) {
    case 'risk_assessment':
      return 'Risk Assessment Report';
    case 'technical_documentation':
      return 'Technische Dokumentation';
    case 'conformity_declaration':
      return 'EU-Konformitätserklärung';
    default:
      return type;
  }
};

// ==================== DOCUMENT UPLOAD ====================

export interface UploadedDocument extends GeneratedDocument {
  filename?: string;
  file_size?: number;
}

export const uploadDocumentation = async (
  systemId: string,
  file: File,
  documentType: string,
  title?: string
): Promise<{ success: boolean; document: UploadedDocument }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('document_type', documentType);
  if (title) {
    formData.append('title', title);
  }
  
  const response = await aiApiClient.post(
    `/api/ai/systems/${systemId}/documentation/upload`,
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  );
  return response.data;
};

export const deleteDocumentation = async (docId: string): Promise<{ success: boolean }> => {
  const response = await aiApiClient.delete(`/api/ai/documentation/${docId}`);
  return response.data;
};

export const getDocumentVersions = async (
  docId: string
): Promise<{ versions: GeneratedDocument[] }> => {
  const response = await aiApiClient.get(`/api/ai/documentation/${docId}/versions`);
  return response.data;
};

export const downloadUploadedFile = async (filePath: string): Promise<Blob> => {
  const response = await aiApiClient.get(`/api/ai/documentation/file/${filePath}`, {
    responseType: 'blob'
  });
  return response.data;
};

// ==================== NOTIFICATIONS ====================

export interface AINotification {
  id: string;
  ai_system_id: string | null;
  type: string;
  severity: 'info' | 'warning' | 'critical';
  title: string;
  message: string;
  metadata: Record<string, any>;
  is_read: boolean;
  created_at: string;
}

export interface AlertSettings {
  email_on_compliance_drop: boolean;
  email_on_high_risk: boolean;
  email_on_scan_reminder: boolean;
  email_on_scan_completed: boolean;
  compliance_drop_threshold: number;
  scan_reminder_days: number;
  inapp_notifications: boolean;
}

export const getNotifications = async (
  unreadOnly: boolean = false,
  limit: number = 50
): Promise<{ notifications: AINotification[]; unread_count: number }> => {
  const response = await aiApiClient.get('/api/ai/notifications', {
    params: { unread_only: unreadOnly, limit }
  });
  return response.data;
};

export const markNotificationRead = async (notificationId: string): Promise<void> => {
  await aiApiClient.put(`/api/ai/notifications/${notificationId}/read`);
};

export const markAllNotificationsRead = async (): Promise<void> => {
  await aiApiClient.put('/api/ai/notifications/read-all');
};

export const getAlertSettings = async (): Promise<AlertSettings> => {
  const response = await aiApiClient.get('/api/ai/settings/alerts');
  return response.data;
};

export const updateAlertSettings = async (settings: Partial<AlertSettings>): Promise<void> => {
  await aiApiClient.put('/api/ai/settings/alerts', settings);
};

// ==================== SCHEDULED SCANS ====================

export interface ScheduledScan {
  id: string;
  schedule_type: 'daily' | 'weekly' | 'monthly';
  schedule_day: number | null;
  schedule_hour: number;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
}

export const createScheduledScan = async (
  systemId: string,
  scheduleType: 'daily' | 'weekly' | 'monthly',
  scheduleDay?: number,
  scheduleHour: number = 9
): Promise<{ success: boolean; schedule: ScheduledScan }> => {
  const response = await aiApiClient.post(`/api/ai/systems/${systemId}/schedule`, {
    schedule_type: scheduleType,
    schedule_day: scheduleDay,
    schedule_hour: scheduleHour
  });
  return response.data;
};

export const getScheduledScan = async (systemId: string): Promise<{ schedule: ScheduledScan | null }> => {
  const response = await aiApiClient.get(`/api/ai/systems/${systemId}/schedule`);
  return response.data;
};

export const deleteScheduledScan = async (systemId: string): Promise<void> => {
  await aiApiClient.delete(`/api/ai/systems/${systemId}/schedule`);
};

// ==================== HELPER FUNCTIONS ====================

export const getRiskCategoryColor = (category: string): string => {
  switch (category) {
    case 'prohibited':
      return 'red';
    case 'high':
      return 'orange';
    case 'limited':
      return 'yellow';
    case 'minimal':
      return 'green';
    case 'pending':
      return 'gray';
    default:
      return 'gray';
  }
};

export const getRiskCategoryLabel = (category: string): string => {
  switch (category) {
    case 'prohibited':
      return 'Verboten';
    case 'high':
      return 'Hochrisiko';
    case 'limited':
      return 'Begrenztes Risiko';
    case 'minimal':
      return 'Minimales Risiko';
    case 'pending':
      return 'Ausstehend';
    default:
      return 'Unbekannt';
  }
};

export const getComplianceScoreColor = (score: number): string => {
  if (score >= 80) return 'green';
  if (score >= 60) return 'yellow';
  if (score >= 40) return 'orange';
  return 'red';
};

export const getComplianceScoreLabel = (score: number): string => {
  if (score >= 80) return 'Gut';
  if (score >= 60) return 'Akzeptabel';
  if (score >= 40) return 'Verbesserungsbedarf';
  return 'Kritisch';
};

