import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import {
  getAccessToken,
  refreshAccessToken,
  clearAccessToken,
} from "@/lib/auth-refresh";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

let _client: AxiosInstance | null = null;

let _isRefreshing = false;
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
        clearAccessToken();
        if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
          try {
            const { signOut } = await import("next-auth/react");
            await signOut({ callbackUrl: "/login" });
          } catch {
            window.location.href = "/login";
          }
        }
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
