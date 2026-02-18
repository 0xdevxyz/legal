import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Intelligente API-URL-Erkennung
const getApiBase = () => {
  // 1. Environment-Variable hat Priorität
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 2. Für Browser: Prüfe Hostname
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8002';
    }
    if (hostname.includes('complyo.tech')) {
      return 'https://api.complyo.tech';
    }
  }
  
  // 3. Fallback für lokale Entwicklung
  return 'http://localhost:8002';
};

const API_BASE = getApiBase();

interface User {
    id: number;
    email: string;
    full_name: string;
    company?: string;
    plan_type?: 'free' | 'ai' | 'expert';
    plan_limits?: {
        websites_max: number;
        exports_max: number;
        websites_count: number;
        exports_this_month: number;
        fixes_used: number;       // Anzahl verwendeter Fixes
        fixes_limit: number;      // Max. erlaubte Fixes (free=1, ai=unlimited)
    };
}

interface RegisterData {
    email: string;
    password: string;
    full_name: string;
    company?: string;
    plan: string;
    modules?: string[];
}

interface AuthContextType {
    user: User | null;
    accessToken: string | null;
    login: (email: string, password: string) => Promise<void>;
    register: (data: RegisterData) => Promise<void>;
    logout: () => void;
    isAuthenticated: boolean;
    isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<User | null>(null);
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    
    // Auto-Refresh Token alle 50 Minuten (Token läuft nach 60 Minuten ab)
    useEffect(() => {
        if (!accessToken) return;
        
        const refreshTokenWithRetry = async (retries = 3): Promise<boolean> => {
            const refreshToken = localStorage.getItem('refresh_token');
            if (!refreshToken) return false;
            
            for (let i = 0; i < retries; i++) {
                try {
                    // ✅ Timeout für Request (10 Sekunden)
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 10000);
                    
                    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ refresh_token: refreshToken }),
                        signal: controller.signal,
                    });
                    
                    clearTimeout(timeoutId);
                    
                    if (response.ok) {
                        const data = await response.json();
                        setAccessToken(data.access_token);
                        localStorage.setItem('access_token', data.access_token);
                        // ✅ SSR-Check
                        if (typeof document !== 'undefined') {
                            document.cookie = `access_token=${data.access_token}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax; Secure`;
                        }
                        return true;
                    }
                    
                    // ✅ Bei 401: Token ungültig, nicht retry
                    if (response.status === 401) {
                        console.log('Refresh token invalid, logging out');
                        logout();
                        return false;
                    }
                    
                    // ✅ Bei anderen Fehlern: Retry mit exponential backoff
                    if (i < retries - 1) {
                        const delay = 1000 * Math.pow(2, i); // 1s, 2s, 4s
                        console.log(`Token refresh failed, retrying in ${delay}ms... (attempt ${i + 1}/${retries})`);
                        await new Promise(resolve => setTimeout(resolve, delay));
                        continue;
                    }
                } catch (error: any) {
                    // ✅ Netzwerk-Fehler: Retry
                    if (error.name === 'AbortError' || error.name === 'TypeError' || error.message?.includes('fetch')) {
                        if (i < retries - 1) {
                            const delay = 1000 * Math.pow(2, i); // 1s, 2s, 4s
                            console.log(`Network error during token refresh, retrying in ${delay}ms... (attempt ${i + 1}/${retries})`);
                            await new Promise(resolve => setTimeout(resolve, delay));
                            continue;
                        }
                    }
                    
                    // ✅ Letzter Versuch fehlgeschlagen
                    if (i === retries - 1) {
                        console.error('Token refresh failed after all retries:', error);
                        // ✅ Nicht sofort ausloggen bei Netzwerk-Fehlern
                        // User kann noch arbeiten, Token wird beim nächsten Request refreshed
                        return false;
                    }
                }
            }
            return false;
        };
        
        const refreshInterval = setInterval(async () => {
            await refreshTokenWithRetry();
        }, 50 * 60 * 1000); // 50 minutes
        
        return () => clearInterval(refreshInterval);
    }, [accessToken]);
    
    useEffect(() => {
        // Load from localStorage on mount
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user');
        if (token && userData) {
            try {
                setAccessToken(token);
                setUser(JSON.parse(userData));
            } catch (e) {
                console.error('Error parsing user data:', e);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('user');
            }
        }
        setIsLoading(false);
    }, []);
    
    const login = async (email: string, password: string) => {
        const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password }),
            credentials: 'include' // Important for cookies
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Login fehlgeschlagen');
        }
        
        const data = await response.json();
        setAccessToken(data.access_token);
        setUser(data.user);
        
        // Store in localStorage
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        // Also store as cookie for middleware (30 days)
        // ✅ SSR-Check
        if (typeof document !== 'undefined') {
            document.cookie = `access_token=${data.access_token}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax; Secure`;
        }
    };
    
    const register = async (data: RegisterData) => {
        const response = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            credentials: 'include'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registrierung fehlgeschlagen');
        }
        
        const result = await response.json();
        setAccessToken(result.access_token);
        setUser(result.user);
        
        // Store in localStorage
        localStorage.setItem('access_token', result.access_token);
        localStorage.setItem('refresh_token', result.refresh_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Also store as cookie for middleware
        // ✅ SSR-Check
        if (typeof document !== 'undefined') {
            document.cookie = `access_token=${result.access_token}; path=/; max-age=${60 * 60 * 24 * 30}; SameSite=Lax; Secure`;
        }
    };
    
    const logout = () => {
        setAccessToken(null);
        setUser(null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        // Delete cookie
        // ✅ SSR-Check
        if (typeof document !== 'undefined') {
            document.cookie = 'access_token=; path=/; max-age=0';
        }
    };
    
    return (
        <AuthContext.Provider value={{ 
            user, 
            accessToken, 
            login, 
            register, 
            logout, 
            isAuthenticated: !!user,
            isLoading 
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};

