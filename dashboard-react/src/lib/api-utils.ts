/**
 * Zentrale API-URL Utility
 * 
 * Erkennt automatisch die richtige API-URL basierend auf:
 * 1. Environment-Variable NEXT_PUBLIC_API_URL
 * 2. Browser-Hostname (localhost → lokaler Backend)
 * 3. Production Domain → Production API
 */

export function getApiBaseUrl(): string {
  // 1. Environment-Variable hat höchste Priorität
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 2. Für Browser: Intelligente Erkennung basierend auf Hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    
    // Localhost → lokaler Backend (HTTP, kein SSL-Problem)
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8002';
    }
    
    // Production Domain → Production API
    if (hostname.includes('complyo.tech')) {
      return 'https://api.complyo.tech';
    }
  }
  
  // 3. Fallback für Server-Side Rendering oder unbekannte Domains
  return 'http://localhost:8002';
}

// Export als Konstante für einfache Verwendung
export const API_BASE_URL = getApiBaseUrl();
