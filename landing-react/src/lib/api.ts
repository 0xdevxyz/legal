import axios from 'axios';
import { ComplianceAnalysis, ApiResponse } from '@/types/api';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use((config) => {
  // Add auth token if available
  const token = localStorage.getItem('complyo_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export const complianceApi = {
  analyzeWebsite: async (url: string): Promise<ComplianceAnalysis> => {
    const response = await api.post<ComplianceAnalysis>('/api/analyze', { url });
    return response.data;
  },

  getDashboardData: async (): Promise<any> => {
    const response = await api.get('/api/dashboard/overview');
    return response.data;
  },

  startAIFix: async (issueId: string): Promise<any> => {
    const response = await api.post(`/api/ai/start-fixes/${issueId}`);
    return response.data;
  },

  bookExpertConsultation: async (issueId: string): Promise<any> => {
    const response = await api.post(`/api/expert/schedule/${issueId}`);
    return response.data;
  },

  getLegalNews: async (): Promise<any> => {
    const response = await api.get('/api/legal/news');
    return response.data;
  }
};

export default api;
