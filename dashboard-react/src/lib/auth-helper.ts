/**
 * @deprecated Use functions from '@/lib/auth-refresh' instead.
 * This module is kept for backwards compatibility only.
 */
export {
  getAccessToken,
  setAccessToken,
  clearAccessToken,
} from "@/lib/auth-refresh";

/**
 * @deprecated Use apiClient from '@/lib/api-client' instead.
 * This function does NOT handle token refresh.
 */
export function getAuthHeaders(): Record<string, string> {
  const { getAccessToken } = require("@/lib/auth-refresh");
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}
