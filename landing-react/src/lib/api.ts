import axios from 'axios';
import { ComplianceAnalysis, ApiResponse, WaitlistJoinRequest, WaitlistJoinResponse, WaitlistPlaetze } from '@/types/api';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.de',
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
 * Akzeptiert: https://, http://, www., nur domain (z.B. complyo.de)
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
    // ✅ FIX: Verwende /api/analyze-preview für Landing-Seite (keine Auth erforderlich)
    // Ein echter Scan braucht 20-27s (gemessen 12.08.2026), der Default von
    // 30s lag also mitten in der Streuung: Kundenseiten brachen sporadisch ab
    // und der Besucher las, SEINE Seite sei nicht erreichbar. 65s deckt den
    // Scan ab und bleibt über dem proxy_read_timeout von nginx (60s), damit
    // ein Überschreiten als Serverfehler ankommt und nicht als Client-Timeout.
    const response = await api.post<ComplianceAnalysis>('/api/analyze-preview', { url: normalizedUrl }, { timeout: 65000 });
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

export const leadsApi = {
  joinWaitlist: async (payload: WaitlistJoinRequest): Promise<WaitlistJoinResponse> => {
    const response = await api.post<WaitlistJoinResponse>('/api/leads/waitlist', payload);
    return response.data;
  },

  // Kurzer Timeout: der Zaehler ist Beiwerk. Antwortet er nicht, soll die Seite
  // das Angebot ohne Zahl zeigen und nicht auf einen Ladebalken warten.
  waitlistPlaetze: async (): Promise<WaitlistPlaetze> => {
    const response = await api.get<WaitlistPlaetze>('/api/leads/waitlist/plaetze', { timeout: 5000 });
    return response.data;
  },
};

export default api;
