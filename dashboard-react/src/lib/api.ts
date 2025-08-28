import axios, { AxiosResponse } from 'axios';
import type { ComplianceAnalysis } from '@/types/api';

// ✅ API Client Configuration
const apiClient = axios.create({
 baseURL: 'https://api.complyo.tech',
 timeout: 30000,
 withCredentials: true,
 headers: {
   'Content-Type': 'application/json',
   'Accept': 'application/json',
 },
});

// ✅ Request/Response Interceptors für Debugging
apiClient.interceptors.request.use(
 (config) => {
   console.log('🔗 API Request:', {
     method: config.method?.toUpperCase(),
     url: config.url,
     baseURL: config.baseURL,
     headers: config.headers,
     data: config.data,
   });
   return config;
 },
 (error) => {
   console.error('💥 API Request Error:', error);
   return Promise.reject(error);
 }
);

apiClient.interceptors.response.use(
 (response) => {
   console.log('✅ API Response:', {
     status: response.status,
     statusText: response.statusText,
     headers: response.headers,
     data: response.data,
   });
   return response;
 },
 (error) => {
   console.error('💥 API Response Error:', {
     status: error.response?.status,
     statusText: error.response?.statusText,
     data: error.response?.data,
     message: error.message,
   });
   return Promise.reject(error);
 }
);

// ✅ URL Validation Helper
const validateAndNormalizeUrl = (url: string): string => {
 if (!url || typeof url !== 'string') {
   throw new Error('URL must be a non-empty string');
 }

 const trimmed = url.trim();
 if (!trimmed) {
   throw new Error('URL cannot be empty or whitespace only');
 }

 console.log('🔍 Starting website analysis for:', trimmed);

 let normalizedUrl = trimmed;
 normalizedUrl = normalizedUrl.replace(/^https?:\/\//, '');
 normalizedUrl = normalizedUrl.replace(/\/$/, '');

 const domainPattern = /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})$/;
 const domainWithPathPattern = /^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}|[a-zA-Z]{2,}\.[a-zA-Z]{2,})(\/.*)?$/;

 if (!domainPattern.test(normalizedUrl) && !domainWithPathPattern.test(normalizedUrl)) {
   if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
     try {
       const urlObj = new URL(trimmed);
       normalizedUrl = urlObj.hostname;
     } catch {
       throw new Error('Invalid URL format. Please provide a valid domain (e.g., example.com)');
     }
   } else {
     throw new Error('Invalid URL format. Please provide a valid domain (e.g., example.com)');
   }
 }

 console.log('🔄 Normalized URL:', normalizedUrl);
 return normalizedUrl;
};

// ✅ Website Analysis API Call
export const analyzeWebsite = async (url: string): Promise<ComplianceAnalysis> => {
 try {
   const normalizedUrl = validateAndNormalizeUrl(url);
   const payload = { url: normalizedUrl };
   console.log('📤 Sending payload:', payload);

   const response: AxiosResponse<ComplianceAnalysis> = await apiClient.post('/api/analyze', payload);

   if (!response.data) {
     throw new Error('No data received from analysis API');
   }

   return response.data;
 } catch (error) {
   console.error('💥 analyzeWebsite failed:', error);

   if (axios.isAxiosError(error)) {
     const status = error.response?.status;
     const message = error.response?.data?.detail || error.message;

     switch (status) {
       case 422:
         throw new Error(`Validation Error: ${message}. Please check the URL format.`);
       case 400:
         throw new Error(`Bad Request: ${message}`);
       case 500:
         throw new Error('Server Error: Please try again later.');
       case 404:
         throw new Error('API endpoint not found. Please contact support.');
       default:
         throw new Error(`API Error (${status}): ${message}`);
     }
   }

   throw error;
 }
};

// ✅ AI Fix API Call
export const startAIFix = async (issueId: string): Promise<any> => {
 try {
   if (!issueId || !issueId.trim()) {
     throw new Error('Issue ID is required');
   }

   const response = await apiClient.post(
     `/api/ai/start-fixes/${encodeURIComponent(issueId.trim())}`
   );

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

export default apiClient;
