import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import {
  getAccessToken,
  refreshAccessToken,
  clearAccessToken,
} from "@/lib/auth-refresh";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

let _client: AxiosInstance | null = null;

let _isRefreshing = false;

// Laeuft gerade eine Abmeldung? Bis zum 09.09. startete JEDE fehlgeschlagene
// Anfrage ihre eigene: nach laengerer Untaetigkeit laufen ein Dutzend Abfragen
// gleichzeitig in 401, und jede rief signOut() samt Weiterleitung auf. Der
// Nutzer sah den Ladebalken rund zwanzigmal, bevor er am Login ankam — es sah
// kaputt aus, obwohl nur eine abgelaufene Sitzung dahintersteckte.
let _isLoggingOut = false;

// Dieselbe Buendelung fuer die Sitzungsabfrage. resolveAccessToken() laeuft vor
// JEDER Anfrage; ohne Token holte jede einzelne ihre eigene next-auth-Sitzung
// (Netzabruf, bis zu 3 s Wartezeit). Zwoelf parallele Abfragen ergaben zwoelf
// Sitzungsabrufe, die alle dasselbe Ergebnis hatten.
let _inflightSession: Promise<string | null> | null = null;
let _pendingRequests: Array<{
  resolve: (token: string | null) => void;
  reject: (err: unknown) => void;
}> = [];

function _onRefreshDone(token: string | null): void {
  _pendingRequests.forEach(({ resolve }) => resolve(token));
  _pendingRequests = [];
}

function _onRefreshFail(err: unknown): void {
  _pendingRequests.forEach(({ reject }) => reject(err));
  _pendingRequests = [];
}

async function resolveAccessToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  const cached = getAccessToken();
  if (cached) return cached;
  // Wer sich gerade abmeldet, braucht keine Sitzung mehr zu suchen.
  if (_isLoggingOut) return null;
  if (_inflightSession) return _inflightSession;
  _inflightSession = _holeSitzungsToken().finally(() => {
    _inflightSession = null;
  });
  return _inflightSession;
}

async function _holeSitzungsToken(): Promise<string | null> {
  try {
    const { getSession } = await import("next-auth/react");
    const timeout = new Promise<null>((resolve) =>
      setTimeout(() => resolve(null), 3000)
    );
    const session = await Promise.race([getSession(), timeout]);
    const token = (session as any)?.accessToken ?? null;
    if (token) {
      const { setAccessToken } = await import("@/lib/auth-refresh");
      setAccessToken(token);
    }
    return token;
  } catch {
    return null;
  }
}
/**
 * Zeitlimit fuer die langlaufenden Auswertungen (Scan, KI-Fix).
 *
 * Der Scan-Endpunkt raeumt sich serverseitig 300 s ein. Ein Client, der schon
 * nach 60 s aufgibt, wirft ein Ergebnis weg, das gerade erzeugt wird — der
 * Nutzer sieht einen Fehler, obwohl der Scan durchlaeuft. Etwas Luft oben
 * drauf, damit die Antwort noch ankommt.
 */
export const LANGLAEUFER_TIMEOUT_MS = 330_000;

/**
 * Abmelden — genau einmal, egal wie viele Anfragen gleichzeitig in 401 laufen.
 *
 * Der Riegel faellt VOR dem ersten await: signOut() holt erst ein CSRF-Token
 * und schickt dann einen POST, dazwischen liegen zwei Netzabrufe. Ohne den
 * Riegel kamen in dieser Luecke alle uebrigen Anfragen durch und starteten
 * dieselbe Abmeldung noch einmal.
 */
async function _abmelden(): Promise<void> {
  if (_isLoggingOut) return;
  _isLoggingOut = true;

  clearAccessToken();

  if (typeof window === "undefined") return;
  if (window.location.pathname.startsWith("/login")) return;

  try {
    const { signOut } = await import("next-auth/react");
    await signOut({ callbackUrl: "/login" });
  } catch {
    window.location.href = "/login";
  }
}

export function getApiClient(): AxiosInstance {
  if (_client) return _client;

  _client = axios.create({
    baseURL: API_URL,
    timeout: 60_000,
    withCredentials: true,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
  });

  _client.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
    const token = await resolveAccessToken();
    if (token) {
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    if (typeof document !== "undefined") {
      const csrf = document.cookie
        .split("; ")
        .find((row) => row.startsWith("csrf_token="))
        ?.split("=")[1];
      if (csrf) config.headers["X-CSRF-Token"] = csrf;
    }
    return config;
  });

  _client.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config;

      if (error.response?.status === 401 && !original._retry) {
        original._retry = true;

        if (_isRefreshing) {
          return new Promise((resolve, reject) => {
            _pendingRequests.push({ resolve, reject });
          }).then((newToken) => {
            if (newToken) {
              original.headers["Authorization"] = `Bearer ${newToken}`;
              return _client!(original);
            }
            return Promise.reject(error);
          });
        }

        _isRefreshing = true;
        const newToken = await refreshAccessToken();
        _isRefreshing = false;

        if (newToken) {
          _onRefreshDone(newToken);
          original.headers["Authorization"] = `Bearer ${newToken}`;
          return _client!(original);
        }

        _onRefreshFail(error);
        await _abmelden();
        return Promise.reject(error);
      }

      const status = error.response?.status;
      if (status >= 500 || (status === 401 && original._retry)) {
        console.warn("[api-client] Error:", {
          status,
          url: original?.url,
          message: error.message,
        });
      }
      return Promise.reject(error);
    }
  );

  return _client;
}

export const apiClient = {
  get: <T = unknown>(url: string, params?: Record<string, unknown>) =>
    getApiClient()
      .get<T>(url, { params })
      .then((r) => r.data),
  post: <T = unknown>(url: string, data?: unknown) =>
    getApiClient()
      .post<T>(url, data)
      .then((r) => r.data),
  put: <T = unknown>(url: string, data?: unknown) =>
    getApiClient()
      .put<T>(url, data)
      .then((r) => r.data),
  patch: <T = unknown>(url: string, data?: unknown) =>
    getApiClient()
      .patch<T>(url, data)
      .then((r) => r.data),
  delete: <T = unknown>(url: string) =>
    getApiClient()
      .delete<T>(url)
      .then((r) => r.data),
};
