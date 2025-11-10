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

/**
 * Normalisiert URLs zu vollständigen https:// URLs
 * Akzeptiert: https://, http://, www., nur domain (z.B. complyo.tech)
 * Entfernt trailing slashes für saubere URLs
 */
const normalizeUrl = (input: string): string => {
  if (!input || typeof input !== 'string') {
    throw new Error('Ungültige URL');
  }

  let cleaned = input.trim().toLowerCase(); // FIXED: toLowerCase für Konsistenz
  
  if (!cleaned) {
    throw new Error('URL darf nicht leer sein');
  }

  // Protokoll hinzufügen wenn nötig
  if (!cleaned.startsWith('http://') && !cleaned.startsWith('https://')) {
    if (cleaned.startsWith('www.')) {
      cleaned = 'https://' + cleaned;
    } else {
      cleaned = 'https://' + cleaned;
    }
  }

  // URL-Objekt für saubere Normalisierung
  try {
    const urlObj = new URL(cleaned);
    // WICHTIG: protocol + hostname (OHNE urlObj.href!)
    // href fügt automatisch / hinzu
    // hostname ist bereits lowercase durch URL-Parser
    
    // FIXED: Entferne www. Präfix für konsistente Hashes
    let hostname = urlObj.hostname;
    if (hostname.startsWith('www.')) {
      hostname = hostname.substring(4);
    }
    
    let normalized = `${urlObj.protocol}//${hostname}`;
    
    // Optional: Port hinzufügen wenn vorhanden und nicht Standard
    if (urlObj.port && urlObj.port !== '80' && urlObj.port !== '443') {
      normalized += `:${urlObj.port}`;
    }
    
    // Optional: Pathname hinzufügen (ohne trailing slash)
    // WICHTIG: Immer den pathname entfernen für konsistente Hashes
    if (urlObj.pathname && urlObj.pathname !== '/' && urlObj.pathname !== '') {
      normalized += urlObj.pathname.replace(/\/+$/, '');
    }
    
    return normalized;
  } catch (e) {
    throw new Error('Ungültiges URL-Format');
  }
};

export const complianceApi = {
  analyzeWebsite: async (url: string): Promise<ComplianceAnalysis> => {
    // Normalisiere URL vor dem API-Call
    const normalizedUrl = normalizeUrl(url);
    console.log('🔗 Landing API - Original:', url, '→ Normalized:', normalizedUrl);
    const response = await api.post<ComplianceAnalysis>('/api/analyze', { url: normalizedUrl });
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
