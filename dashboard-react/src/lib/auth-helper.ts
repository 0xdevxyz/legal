export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return (
    (window as any).__complyo_access_token ||
    localStorage.getItem('access_token') ||
    null
  );
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAccessToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}
