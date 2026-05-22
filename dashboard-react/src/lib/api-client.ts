import axios, { type AxiosInstance } from "axios";
import { getSession } from "next-auth/react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8002";

let _client: AxiosInstance | null = null;

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

  _client.interceptors.request.use(async (config) => {
    if (typeof window !== "undefined") {
      const token =
        (window as any).__complyo_access_token ||
        (await getSession().then((s) => s?.accessToken ?? null));
      if (token) {
        config.headers["Authorization"] = `Bearer ${token}`;
      }
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
        const session = await getSession();
        if (session?.accessToken) {
          original.headers["Authorization"] = `Bearer ${session.accessToken}`;
          return _client!(original);
        }
        if (typeof window !== "undefined") {
          window.location.href = "/login";
        }
      }
      return Promise.reject(error);
    }
  );

  return _client;
}

export const apiClient = {
  get: <T = unknown>(url: string, params?: Record<string, unknown>) =>
    getApiClient().get<T>(url, { params }).then((r) => r.data),
  post: <T = unknown>(url: string, data?: unknown) =>
    getApiClient().post<T>(url, data).then((r) => r.data),
  put: <T = unknown>(url: string, data?: unknown) =>
    getApiClient().put<T>(url, data).then((r) => r.data),
  patch: <T = unknown>(url: string, data?: unknown) =>
    getApiClient().patch<T>(url, data).then((r) => r.data),
  delete: <T = unknown>(url: string) =>
    getApiClient().delete<T>(url).then((r) => r.data),
};
