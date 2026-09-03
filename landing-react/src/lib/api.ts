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

// Wie oft und wie lange nach dem Ergebnis gefragt wird.
//
// Ein Scan dauert gemessen 16-18 s allein, unter Last von 40 gleichzeitigen
// Auftraegen bis 141 s. Die Obergrenze liegt bewusst darueber: lieber ein paar
// Sekunden zu lange warten als einem Besucher zu sagen, seine Seite sei nicht
// pruefbar, waehrend das Ergebnis eine Sekunde spaeter eintrifft.
const ABHOL_ABSTAND_MS = 2000;
const ABHOL_MAX_MS = 240000;

async function holeErgebnis(
  kennung: string,
  aufZustand?: (zustand: string) => void,
): Promise<ComplianceAnalysis> {
  const beginn = Date.now();
  let letzterZustand = '';

  while (Date.now() - beginn < ABHOL_MAX_MS) {
    const antwort = await api.get<any>(`/api/analyze-auftrag/${kennung}`, { timeout: 15000 });
    const daten = antwort.data || {};

    if (daten.zustand && daten.zustand !== letzterZustand) {
      letzterZustand = daten.zustand;
      aufZustand?.(daten.zustand);
    }

    if (daten.zustand === 'fertig') {
      return daten.ergebnis as ComplianceAnalysis;
    }
    // `fertig: true` heisst "hoer auf zu fragen", nicht "hat geklappt".
    if (daten.zustand === 'fehlgeschlagen') {
      throw new Error(daten.fehler || 'Die Prüfung ist fehlgeschlagen.');
    }

    await new Promise((r) => setTimeout(r, ABHOL_ABSTAND_MS));
  }

  throw new Error(
    'Die Prüfung dauert ungewöhnlich lange. Bitte versuchen Sie es später erneut.',
  );
}

export const complianceApi = {
  analyzeWebsite: async (
    url: string,
    aufZustand?: (zustand: string) => void,
  ): Promise<ComplianceAnalysis> => {
    const normalizedUrl = normalizeUrl(url);

    // Entkoppelter Weg zuerst: Auftrag abgeben, Kennung bekommen, Ergebnis
    // abholen. Die Annahme dauert Millisekunden statt der 16-18 s eines
    // Scans.
    //
    // Warum das mehr ist als Kosmetik (gemessen 03./04.09.2026): solange die
    // Anfrage offen stand, wuchs der Speicher des Backends mit der Zahl der
    // WARTENDEN Anfragen. Bei 22 gleichzeitigen Scans lieferten vier davon
    // 14 statt 13 Befunde — dieselbe Seite, anderes Ergebnis, je nach Last.
    // Entkoppelt brauchen 40 gleichzeitige Auftraege weniger Speicher als
    // vorher 22 (1.318 statt 2.047 MiB), keiner wird abgelehnt, alle liefern
    // dasselbe.
    //
    // Der synchrone Weg bleibt als Rueckfall: faellt Redis aus, antwortet die
    // Annahme mit 503, und es waere absurd, dem Besucher dann gar keinen Scan
    // anzubieten, obwohl der Scanner laeuft.
    try {
      const auftrag = await api.post<{ kennung: string }>(
        '/api/analyze-auftrag', { url: normalizedUrl }, { timeout: 15000 },
      );
      const kennung = auftrag.data?.kennung;
      if (kennung) {
        return await holeErgebnis(kennung, aufZustand);
      }
    } catch (e: any) {
      // 503 = entkoppelter Weg gerade nicht verfuegbar. Alles andere (Netz,
      // 4xx) soll ebenfalls nicht den ganzen Scan verhindern, solange der
      // synchrone Weg noch existiert.
      console.warn('Entkoppelter Scan nicht moeglich, nehme den synchronen Weg', e?.message);
    }

    // Rueckfall: ein echter Scan braucht 16-27 s. 65 s deckt ihn ab und bleibt
    // ueber dem proxy_read_timeout von nginx, damit ein Ueberschreiten als
    // Serverfehler ankommt und nicht als Client-Timeout.
    const response = await api.post<ComplianceAnalysis>(
      '/api/analyze-preview', { url: normalizedUrl }, { timeout: 65000 },
    );
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

  // Signiertes Formular-Token. Wer es nicht vorlegt, wird beim Absenden still
  // verworfen — deshalb holt das Formular es direkt beim Anzeigen und nicht
  // erst beim Klick, damit die Wartezeit nicht auf den Absendevorgang faellt.
  waitlistToken: async (): Promise<string> => {
    const response = await api.get<{ token: string }>('/api/leads/waitlist/token', { timeout: 8000 });
    return response.data.token;
  },

  // Kurzer Timeout: der Zaehler ist Beiwerk. Antwortet er nicht, soll die Seite
  // das Angebot ohne Zahl zeigen und nicht auf einen Ladebalken warten.
  waitlistPlaetze: async (): Promise<WaitlistPlaetze> => {
    const response = await api.get<WaitlistPlaetze>('/api/leads/waitlist/plaetze', { timeout: 5000 });
    return response.data;
  },
};

export default api;
