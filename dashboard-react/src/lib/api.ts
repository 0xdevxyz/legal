import axios, { AxiosResponse } from 'axios';
import type { ComplianceAnalysis, FixResult, UserLimits, FixHistory } from '@/types/api';

// ✅ API Client Configuration - Dynamische URL zur Runtime
const getApiBaseURL = () => {
  // 1. Wenn Umgebungsvariable gesetzt ist, diese verwenden
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 2. Für Browser: Intelligente URL-Erkennung
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // Localhost → lokaler Backend
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8002';
    }
    
    // Production Domain → API-Subdomain
    if (hostname.includes('complyo.tech')) {
      return 'https://api.complyo.tech';
    }
  }
  
  // 3. Fallback für Server-Side Rendering
  return 'http://localhost:8002';
};

const apiClient = axios.create({
 baseURL: getApiBaseURL(),
 timeout: 30000,
 withCredentials: true,
 headers: {
   'Content-Type': 'application/json',
   'Accept': 'application/json',
 },
});

// ✅ Request Interceptor: Auto-inject Authorization Token
apiClient.interceptors.request.use(
 (config) => {
   // Get token from localStorage
   const token = localStorage.getItem('access_token');
   
  // If token exists, add it to Authorization header
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  
  return config;
 },
 (error) => {
   console.error('💥 API Request Error:', error);
   return Promise.reject(error);
 }
);

apiClient.interceptors.response.use(
 (response) => {
   return response;
 },
 async (error) => {
   const originalRequest = error.config;
   
   // ✅ Retry bei Netzwerk-Fehlern
   if ((error.code === 'ERR_NETWORK' || error.code === 'ERR_NETWORK_CHANGED' || error.message?.includes('fetch')) && !originalRequest._retry) {
     originalRequest._retry = true;
     console.log('Network error detected, retrying request...');
     await new Promise(resolve => setTimeout(resolve, 1000));
     return apiClient(originalRequest);
   }
   
   // ✅ Token-Refresh bei 401
   if (error.response?.status === 401 && !originalRequest._retry) {
     originalRequest._retry = true;
     
     const refreshToken = localStorage.getItem('refresh_token');
     if (refreshToken) {
       try {
         const refreshResponse = await apiClient.post('/api/auth/refresh', {
           refresh_token: refreshToken
         });
         
         const newToken = refreshResponse.data.access_token;
         localStorage.setItem('access_token', newToken);
         originalRequest.headers.Authorization = `Bearer ${newToken}`;
         
         return apiClient(originalRequest);
       } catch (refreshError) {
         // ✅ Refresh fehlgeschlagen → Logout
         console.error('Token refresh failed in interceptor:', refreshError);
         localStorage.removeItem('access_token');
         localStorage.removeItem('refresh_token');
         localStorage.removeItem('user');
         
         // ✅ Redirect zu Login (nur im Browser)
         if (typeof window !== 'undefined') {
           window.location.href = '/login';
         }
         
         return Promise.reject(refreshError);
       }
     } else {
       // ✅ Kein Refresh-Token → Logout
       if (typeof window !== 'undefined') {
         window.location.href = '/login';
       }
     }
   }
   
   console.error('💥 API Response Error:', {
     status: error.response?.status,
     statusText: error.response?.statusText,
     data: error.response?.data,
     message: error.message,
     code: error.code,
   });
   
   return Promise.reject(error);
 }
);

// ✅ URL Validation Helper - Akzeptiert ALLE gängigen Formate
// Unterstützt: https://, http://, www., nur domain (z.B. complyo.tech)
const validateAndNormalizeUrl = (url: string): string => {
 // Type-safe check für undefined/null
 if (!url || typeof url !== 'string') {
   console.error('❌ validateAndNormalizeUrl: Invalid input:', typeof url, url);
   throw new Error('URL must be a non-empty string');
 }

 // Sicher trimmen
 const trimmed = String(url).trim();
 if (!trimmed) {
   throw new Error('URL cannot be empty or whitespace only');
 }

 // Type-safe startsWith Checks
 const hasHttp = trimmed.indexOf('http://') === 0;
 const hasHttps = trimmed.indexOf('https://') === 0;
 const hasWww = trimmed.indexOf('www.') === 0;

 // Protokoll hinzufügen wenn nötig
 let urlToValidate = trimmed;
 if (!hasHttp && !hasHttps) {
   urlToValidate = 'https://' + trimmed;
 }

 // URL parsen und validieren
 try {
   const urlObj = new URL(urlToValidate);
   
   // Einfache Domain-Validierung (mindestens ein Punkt)
   if (!urlObj.hostname.includes('.')) {
     throw new Error('Invalid domain format');
   }
   
   // WICHTIG: protocol + hostname (OHNE urlObj.href!)
   // href fügt automatisch / hinzu
   let normalizedUrl = `${urlObj.protocol}//${urlObj.hostname}`;
   
   // Optional: Port hinzufügen wenn vorhanden und nicht Standard
   if (urlObj.port && urlObj.port !== '80' && urlObj.port !== '443') {
     normalizedUrl += `:${urlObj.port}`;
   }
   
   // Optional: Pathname hinzufügen (ohne trailing slash)
   if (urlObj.pathname && urlObj.pathname !== '/') {
     normalizedUrl += urlObj.pathname.replace(/\/+$/, '');
   }

   return normalizedUrl;
 } catch (error) {
   console.error('URL validation error:', error);
   throw new Error('Ungültiges URL-Format. Bitte geben Sie eine gültige Domain ein (z.B. example.com)');
 }
};

// ✅ Website Analysis API Call
export const analyzeWebsite = async (url: string): Promise<ComplianceAnalysis> => {
 try {
   const normalizedUrl = validateAndNormalizeUrl(url);
   const payload = { url: normalizedUrl };

  // Point to the public analysis endpoint (no auth required for now)
  const response: AxiosResponse<ComplianceAnalysis & { success: boolean }> = await apiClient.post('/api/analyze', payload);

   if (!response.data || !response.data.success) {
     throw new Error('Analysis API did not return a successful response');
   }

   // ✅ Die Daten sind direkt in response.data (nicht verschachtelt!)

   return response.data;
 } catch (error) {
   console.error('💥 analyzeWebsite failed:', error);

   if (axios.isAxiosError(error)) {
     const status = error.response?.status;
     const errorData = error.response?.data;
     
     // ✅ FIX: Parse error detail (kann String oder Object sein)
     let message = 'Unbekannter Fehler';
     let suggestions: string[] = [];
     let details: string | undefined;
     
     if (errorData?.detail) {
       const detail = errorData.detail;
       
       // Wenn detail ein Object ist (strukturierter Error)
       if (typeof detail === 'object' && detail !== null) {
         message = detail.message || detail.error || 'Fehler bei der Analyse';
         suggestions = detail.suggestions || [];
         details = detail.details || detail.error_message;
       } else if (typeof detail === 'string') {
         // Wenn detail ein String ist
         message = detail;
       }
     } else if (errorData?.message) {
       message = errorData.message;
     } else if (error.message) {
       message = error.message;
     }
     
     // ✅ User-freundliche Fehlermeldung mit Suggestions
     let userMessage = message;
     if (suggestions.length > 0) {
       userMessage += '\n\nVorschläge:\n' + suggestions.map(s => `• ${s}`).join('\n');
     }
     if (details) {
       userMessage += `\n\nDetails: ${details}`;
     }

     switch (status) {
       case 422:
         throw new Error(`Validierungsfehler: ${userMessage}`);
       case 400:
         throw new Error(userMessage);
       case 401:
         throw new Error('Nicht autorisiert. Bitte melden Sie sich erneut an.');
       case 500:
         throw new Error('Server-Fehler. Bitte versuchen Sie es später erneut.');
       case 404:
         throw new Error('API-Endpunkt nicht gefunden. Bitte kontaktieren Sie den Support.');
       default:
         throw new Error(`API-Fehler (${status}): ${userMessage}`);
     }
   }

   throw error;
 }
};

// ✅ AI Fix API Call
export const startAIFix = async (scanId: string, categories?: string[]): Promise<any> => {
 try {
   if (!scanId) {
     throw new Error('Scan ID is required');
   }
   
   const payload = {
     scan_id: scanId,
     fix_categories: categories,
   };

   const response = await apiClient.post('/api/v2/ai-fix', payload);

   return response.data;
 } catch (error) {
   console.error('💥 startAIFix failed:', error);

   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`AI Fix Error: ${message}`);
   }

   throw error;
 }
};

// ✅ Expert Booking API Call
export const bookExpertConsultation = async (issueId: string): Promise<any> => {
 try {
   if (!issueId || !issueId.trim()) {
     throw new Error('Issue ID is required');
   }

   const response = await apiClient.post(
     `/api/expert/schedule/${encodeURIComponent(issueId.trim())}`
   );

   return response.data;
 } catch (error) {
   console.error('💥 bookExpertConsultation failed:', error);

   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Expert Booking Error: ${message}`);
   }

   throw error;
 }
};

// ✅ Legal News API Call
export const getLegalNews = async () => {
 try {
   const response = await apiClient.get('/api/legal/news');
   return response.data;
 } catch (error) {
   console.error('💥 getLegalNews failed:', error);

   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Legal News Error: ${message}`);
   }

   throw error;
 }
};

// ✅ Dashboard Overview API Call  
export const getDashboardOverview = async () => {
 try {
   const response = await apiClient.get('/api/dashboard/overview');
   return response.data;
 } catch (error) {
   console.error('💥 getDashboardOverview failed:', error);

   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Dashboard Overview Error: ${message}`);
   }

   throw error;
 }
};

// ✅ Create Checkout Session API Call
export const createCheckoutSession = async (priceId: string, successUrl: string, cancelUrl: string): Promise<any> => {
 try {
   const response = await apiClient.post('/api/v2/payments/create-checkout-session', {
     price_id: priceId,
     success_url: successUrl,
     cancel_url: cancelUrl
   });
   return response.data;
 } catch (error) {
   console.error('💥 createCheckoutSession failed:', error);
   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Checkout Session Error: ${message}`);
   }
   throw error;
 }
};

// ✅ Create Portal Session API Call
export const createPortalSession = async (): Promise<any> => {
 try {
   const response = await apiClient.post('/api/v2/payments/create-portal-session');
   return response.data;
 } catch (error) {
   console.error('💥 createPortalSession failed:', error);
   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Portal Session Error: ${message}`);
   }
   throw error;
 }
};

// ✅ Get Subscription Status API Call
export const getSubscriptionStatus = async (): Promise<any> => {
 try {
   const response = await apiClient.get('/api/v2/payments/subscription-status');
   return response.data;
 } catch (error) {
   console.error('💥 getSubscriptionStatus failed:', error);
   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Subscription Status Error: ${message}`);
   }
   throw error;
 }
};

// ✅ Get Payment History API Call
export const getPaymentHistory = async (): Promise<any> => {
 try {
   const response = await apiClient.get('/api/v2/payments/history');
   return response.data;
 } catch (error) {
   console.error('💥 getPaymentHistory failed:', error);
   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Payment History Error: ${message}`);
   }
   throw error;
 }
};

// ✅ Get Available Plans API Call
export const getAvailablePlans = async (): Promise<any> => {
 try {
   const response = await apiClient.get('/api/v2/payments/plans');
   return response.data;
 } catch (error) {
   console.error('💥 getAvailablePlans failed:', error);
   if (axios.isAxiosError(error)) {
     const message = error.response?.data?.detail || error.message;
     throw new Error(`Available Plans Error: ${message}`);
   }
   throw error;
 }
};

// ✅ Export Fix API Call
export const exportFix = async (fixId: number, exportFormat: string = 'html'): Promise<any> => {
  try {

    const response = await apiClient.post('/api/v2/fixes/export', {
      fix_id: fixId,
      export_format: exportFormat
    });

    return response.data;
  } catch (error) {
    console.error('💥 exportFix failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Fix Export Error: ${message}`);
    }
    throw error;
  }
};

// ✅ Get User Limits API Call
export const getUserLimits = async (): Promise<UserLimits> => {
  try {

    const response: AxiosResponse<UserLimits> = await apiClient.get('/api/v2/fixes/limits');

    return response.data;
  } catch (error) {
    console.error('💥 getUserLimits failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`User Limits Error: ${message}`);
    }
    throw error;
  }
};

// ✅ Get Fix History API Call
export const getFixHistory = async (): Promise<FixHistory> => {
  try {

    const response: AxiosResponse<FixHistory> = await apiClient.get('/api/v2/fixes/history');

    return response.data;
  } catch (error) {
    console.error('💥 getFixHistory failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Fix History Error: ${message}`);
    }
    throw error;
  }
};

// ✅ Website Management API Calls

export interface TrackedWebsite {
  id: number;
  url: string;
  last_score: number;
  last_scan_date: string;
  scan_count: number;
  is_primary: boolean;
}

export const getTrackedWebsites = async (): Promise<TrackedWebsite[]> => {
  try {

    const response: AxiosResponse<{ websites: TrackedWebsite[] }> = await apiClient.get('/api/v2/websites');

    return response.data.websites;
  } catch (error) {
    console.error('💥 getTrackedWebsites failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Website Fetch Error: ${message}`);
    }
    throw error;
  }
};

export const saveTrackedWebsite = async (url: string, score: number): Promise<TrackedWebsite> => {
  try {

    const response: AxiosResponse<{ website: TrackedWebsite }> = await apiClient.post('/api/v2/websites', { url, score });

    return response.data.website;
  } catch (error) {
    console.error('💥 saveTrackedWebsite failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Website Save Error: ${message}`);
    }
    throw error;
  }
};

export const deleteTrackedWebsite = async (websiteId: number): Promise<void> => {
  try {

    await apiClient.delete(`/api/v2/websites/${websiteId}`);

  } catch (error) {
    console.error('💥 deleteTrackedWebsite failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Website Delete Error: ${message}`);
    }
    throw error;
  }
};

/**
 * Generiert einen KI-Fix für ein Issue
 */
export const generateFix = async (issueId: string, issueCategory: string): Promise<FixResult> => {
  try {

    const response: AxiosResponse<{
      success: boolean;
      fix: FixResult;
      first_fix: boolean;
      money_back_warning: boolean;
      plan_type: string;
    }> = await apiClient.post('/api/v2/fixes/generate', {
      issue_id: issueId,
      issue_category: issueCategory
    });

    // Warne wenn Geld-zurück-Garantie verfällt
    if (response.data.money_back_warning) {

    }
    
    return response.data.fix;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;
      const status = error.response?.status;
      
      // Strukturierte Fehlerbehandlung basierend auf Backend-Response
      if (typeof detail === 'object' && detail !== null) {
        const errorObj = detail as any;
        
        // HTTP 400: Invalid Input
        if (status === 400) {
          throw new Error(errorObj.message || 'Ungültige Eingabe');
        }
        
        // HTTP 402: Payment Required (Fix Limit)
        if (status === 402) {
          const err: any = new Error(errorObj.message || 'Fix-Limit erreicht');
          err.code = 'FIX_LIMIT_REACHED';
          err.fixes_used = errorObj.fixes_used;
          err.fixes_limit = errorObj.fixes_limit;
          throw err;
        }
        
        // HTTP 403: Forbidden (Limit Reached)
        if (status === 403) {
          throw new Error(errorObj.message || 'Optimierungs-Limit erreicht! Bitte upgraden Sie Ihren Plan.');
        }
        
        // HTTP 503: Service Unavailable (AI Service Down)
        if (status === 503) {
          throw new Error(errorObj.message || 'KI-Service vorübergehend nicht verfügbar. Bitte versuchen Sie es später erneut.');
        }
        
        // HTTP 504: Timeout
        if (status === 504) {
          throw new Error(errorObj.message || 'Zeitüberschreitung. Bitte versuchen Sie es erneut.');
        }
        
        // HTTP 500: Internal Server Error
        if (status === 500) {
          const supportMsg = errorObj.support_message ? `\n\n${errorObj.support_message}` : '';
          throw new Error((errorObj.message || 'Interner Serverfehler') + supportMsg);
        }
        
        // Allgemeiner strukturierter Fehler
        throw new Error(errorObj.message || 'Ein Fehler ist aufgetreten');
      }
      
      // Fallback für nicht-strukturierte Fehler
      const message = typeof detail === 'string' ? detail : error.message;
      throw new Error(`KI-Fix Fehler: ${message}`);
    }
    throw error;
  }
};

/**
 * Stripe Payment Integration
 */

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface PortalResponse {
  portal_url: string;
}

/**
 * Erstellt eine Stripe Checkout Session für das Upgrade
 * Im DEV_MODE wird die Zahlung simuliert und User direkt upgraded
 */
export const createStripeCheckout = async (
  plan: string = 'pro',
  billingPeriod: string = 'monthly',
  domain?: string,
  successUrl?: string,
  cancelUrl?: string
): Promise<CheckoutResponse & { dev_mode?: boolean; message?: string }> => {
  try {

    const response: AxiosResponse<CheckoutResponse & { dev_mode?: boolean; message?: string }> = await apiClient.post('/api/stripe/create-checkout', {
      plan,
      billing_period: billingPeriod,
      domain, // Domain mitgeben für Domain-Lock
      success_url: successUrl || `${window.location.origin}/dashboard?payment=success&domain=${encodeURIComponent(domain || '')}`,
      cancel_url: cancelUrl || `${window.location.origin}/dashboard?payment=cancelled`
    });

    // DEV_MODE Warnung anzeigen
    if (response.data.dev_mode) {
      console.warn('⚠️ ENTWICKLUNGSMODUS: Zahlung wurde simuliert', response.data.message);
    }

    return response.data;
  } catch (error) {
    console.error('💥 createStripeCheckout failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Stripe Checkout Fehler: ${message}`);
    }
    throw error;
  }
};

/**
 * Erstellt eine Stripe Customer Portal Session für Subscription Management
 */
export const createStripePortal = async (returnUrl?: string): Promise<PortalResponse> => {
  try {

    const response: AxiosResponse<PortalResponse> = await apiClient.post('/api/stripe/create-portal-session', {
      return_url: returnUrl || `${window.location.origin}/dashboard`
    });

    return response.data;
  } catch (error) {
    console.error('💥 createStripePortal failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Stripe Portal Fehler: ${message}`);
    }
    throw error;
  }
};

/**
 * eRecht24 API Integration
 * Bundling: Technische Checks + rechtliche Beschreibungen
 */

export interface ERecht24Project {
  project_id: string;
  api_key: string;
  secret: string;
}

export interface LegalText {
  html_content: string;
  text_type: string;
  language: string;
  created_at: string;
}

export interface ImpressumValidation {
  is_valid: boolean;
  score: number;
  missing_fields: string[];
  recommendations: string[];
}

export interface CookieBannerConfig {
  banner_text: string;
  categories: Array<{
    name: string;
    required: boolean;
    description: string;
  }>;
  cookies: any[];
  script?: string;
}

/**
 * Erstellt ein eRecht24-Projekt für eine Domain
 */
export const createERecht24Project = async (domain: string): Promise<ERecht24Project> => {
  try {

    const response: AxiosResponse<ERecht24Project> = await apiClient.post('/api/v2/erecht24/projects', {
      domain
    });

    return response.data;
  } catch (error) {
    console.error('💥 createERecht24Project failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`eRecht24 Projekt-Erstellung fehlgeschlagen: ${message}`);
    }
    throw error;
  }
};

/**
 * Generiert rechtssichere Texte (Impressum, Datenschutz, AGB)
 */
export const generateLegalText = async (
  projectId: string,
  type: 'impressum' | 'datenschutz' | 'agb',
  companyData: Record<string, any>
): Promise<LegalText> => {
  try {

    const response: AxiosResponse<LegalText> = await apiClient.post(
      `/api/v2/erecht24/legal-text/${type}`,
      {
        project_id: projectId,
        ...companyData
      }
    );

    return response.data;
  } catch (error) {
    console.error('💥 generateLegalText failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Rechtstext-Generierung fehlgeschlagen: ${message}`);
    }
    throw error;
  }
};

/**
 * Validiert ein Impressum auf Vollständigkeit
 */
export const validateImpressum = async (text: string): Promise<ImpressumValidation> => {
  try {

    const response: AxiosResponse<ImpressumValidation> = await apiClient.post(
      '/api/v2/erecht24/validate-impressum',
      { text }
    );

    return response.data;
  } catch (error) {
    console.error('💥 validateImpressum failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Impressum-Validierung fehlgeschlagen: ${message}`);
    }
    throw error;
  }
};

/**
 * Generiert Cookie-Banner-Konfiguration basierend auf erkannten Cookies
 */
export const generateCookieBanner = async (cookies: any[]): Promise<CookieBannerConfig> => {
  try {

    const response: AxiosResponse<CookieBannerConfig> = await apiClient.post(
      '/api/v2/erecht24/cookie-config',
      { cookies }
    );

    return response.data;
  } catch (error) {
    console.error('💥 generateCookieBanner failed:', error);
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.detail || error.message;
      throw new Error(`Cookie-Banner-Generierung fehlgeschlagen: ${message}`);
    }
    throw error;
  }
};

/**
 * Response-Normalizer für robuste Datenverarbeitung
 * Stellt sicher, dass alle API-Responses konsistente Struktur haben
 */

import type { ComplianceIssue } from '@/types/api';

export const normalizeAnalysisResponse = (data: any): ComplianceAnalysis => {
  if (!data || typeof data !== 'object') {
    return createEmptyAnalysis();
  }

  return {
    scan_id: data.scan_id || `scan_${Date.now()}`,
    url: data.url || '',
    compliance_score: normalizeScore(data.compliance_score),
    critical_issues: Math.max(0, data.critical_issues ?? 0),
    warning_issues: Math.max(0, data.warning_issues ?? 0),
    total_issues: Math.max(0, data.total_issues ?? 0),
    total_risk_euro: typeof data.total_risk_euro === 'number' ? data.total_risk_euro : 0,
    issues: normalizeIssues(data.issues),
    positive_checks: Array.isArray(data.positive_checks) ? data.positive_checks : [],
    scan_timestamp: data.scan_timestamp || new Date().toISOString(),
    scan_duration_ms: data.scan_duration_ms || 0,
    recommendations: Array.isArray(data.recommendations) ? data.recommendations : [],
    next_steps: Array.isArray(data.next_steps) ? data.next_steps : []
  };
};

const normalizeScore = (score: any): number => {
  if (typeof score === 'number') {
    return Math.max(0, Math.min(100, score));
  }
  if (typeof score === 'string') {
    const parsed = parseFloat(score);
    return isNaN(parsed) ? 0 : Math.max(0, Math.min(100, parsed));
  }
  return 0;
};

const normalizeIssues = (issues: any): ComplianceIssue[] => {
  if (!Array.isArray(issues)) {
    return [];
  }

  return issues
    .map(issue => normalizeIssue(issue))
    .filter((issue): issue is ComplianceIssue => issue !== null);
};

const normalizeIssue = (issue: any): ComplianceIssue | null => {
  if (!issue) return null;

  // String-Issues zu Objects konvertieren
  if (typeof issue === 'string') {
    const riskEuro = 1000;
    return {
      id: `issue_${Math.random().toString(36).substr(2, 9)}`,
      category: 'compliance',
      severity: 'warning' as const,
      title: issue.substring(0, 100),
      description: issue,
      risk_euro: riskEuro,
      risk_euro_min: riskEuro,
      risk_euro_max: riskEuro * 2,
      risk_range: `${riskEuro}€ - ${riskEuro * 2}€`,
      recommendation: 'Bitte korrigieren Sie diesen Punkt',
      legal_basis: 'DSGVO, TMG',
      location: {
        area: 'Allgemein',
        hint: 'Überprüfen Sie Ihre Website'
      },
      solution: {
        code_snippet: '',
        steps: ['Bitte korrigieren Sie diesen Punkt']
      },
      auto_fixable: false
    };
  }

  // Object-Issues validieren und Defaults setzen
  if (typeof issue === 'object') {
    const riskEuro = Math.max(0, issue.risk_euro ?? issue.risk_euro_min ?? 0);
    return {
      id: issue.id || `issue_${Math.random().toString(36).substr(2, 9)}`,
      category: issue.category || 'compliance',
      severity: normalizeSeverity(issue.severity),
      title: issue.title || 'Compliance-Problem',
      description: issue.description || '',
      risk_euro: riskEuro,
      risk_euro_min: issue.risk_euro_min ?? riskEuro,
      risk_euro_max: issue.risk_euro_max ?? (riskEuro * 2),
      risk_range: issue.risk_range || `${riskEuro}€ - ${riskEuro * 2}€`,
      recommendation: issue.recommendation || '',
      legal_basis: issue.legal_basis || '',
      location: issue.location || {
        area: issue.category || 'Allgemein',
        hint: 'Überprüfen Sie diesen Bereich'
      },
      solution: issue.solution || {
        code_snippet: '',
        steps: issue.recommendation ? [issue.recommendation] : []
      },
      auto_fixable: Boolean(issue.auto_fixable)
    };
  }

  return null;
};

const normalizeSeverity = (severity: any): 'critical' | 'warning' | 'info' => {
  if (typeof severity === 'string') {
    const normalized = severity.toLowerCase();
    if (normalized === 'critical') return 'critical';
    if (normalized === 'info') return 'info';
  }
  return 'warning';
};

const createEmptyAnalysis = (): ComplianceAnalysis => ({
  scan_id: `scan_${Date.now()}`,
  url: '',
  compliance_score: 0,
  critical_issues: 0,
  warning_issues: 0,
  total_issues: 0,
  total_risk_euro: 0,
  issues: [],
  positive_checks: [],
  scan_timestamp: new Date().toISOString(),
  scan_duration_ms: 0,
  recommendations: [],
  next_steps: []
});

/**
 * Input-Validation Helper
 */
export const validateDomain = (domain: string): string => {
  if (!domain || typeof domain !== 'string') {
    throw new Error('Domain muss ein nicht-leerer String sein');
  }

  const trimmed = domain.trim();
  if (!trimmed) {
    throw new Error('Domain darf nicht leer sein');
  }

  // Basic domain validation
  const domainPattern = /^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/;
  const urlPattern = /^https?:\/\/([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}/;

  if (!domainPattern.test(trimmed) && !urlPattern.test(trimmed)) {
    throw new Error('Ungültiges Domain-Format');
  }

  return trimmed;
};

export { apiClient };
export default apiClient;
