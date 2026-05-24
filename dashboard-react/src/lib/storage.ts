const isClient = typeof window !== 'undefined';

export const safeStorage = {
  get: (key: string): string | null => {
    try {
      return isClient ? localStorage.getItem(key) : null;
    } catch {
      return null;
    }
  },
  set: (key: string, value: string): void => {
    try {
      if (isClient) localStorage.setItem(key, value);
    } catch {}
  },
  remove: (key: string): void => {
    try {
      if (isClient) localStorage.removeItem(key);
    } catch {}
  },
  getJSON: <T>(key: string, fallback: T): T => {
    try {
      const item = isClient ? localStorage.getItem(key) : null;
      return item ? (JSON.parse(item) as T) : fallback;
    } catch {
      return fallback;
    }
  },
  setJSON: (key: string, value: unknown): void => {
    try {
      if (isClient) localStorage.setItem(key, JSON.stringify(value));
    } catch {}
  },
};

export const getAuthToken = (): string | null => safeStorage.get('access_token');
