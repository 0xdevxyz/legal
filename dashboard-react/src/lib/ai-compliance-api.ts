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

