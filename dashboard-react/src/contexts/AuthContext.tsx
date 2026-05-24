'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useSession, signIn, signOut } from 'next-auth/react';

interface User {
  id: number;
  email: string;
  full_name: string;
  company?: string;
  plan_type?: 'free' | 'single' | 'pro' | 'agency' | 'expert' | 'update';
  role?: 'admin' | 'agency' | 'customer';
  onboarding_completed?: boolean;
  active_modules?: string[];
  plan_limits?: {
    websites_max: number;
    exports_max: number;
    websites_count: number;
    exports_this_month: number;
    fixes_used: number;
    fixes_limit: number;
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
  isAuthReady: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  markOnboardingCompleted: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { data: session, status, update } = useSession();
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [hasTriedUpdate, setHasTriedUpdate] = useState(false);

  const isLoading = status === 'loading';
  const isAuthenticated = status === 'authenticated';

  const user: User | null = session?.user
    ? {
        id: Number(session.user.id),
        email: session.user.email,
        full_name: session.user.full_name,
        company: session.user.company,
        plan_type: session.user.plan_type as User['plan_type'],
        role: session.user.role as User['role'],
        onboarding_completed: session.user.onboarding_completed,
        active_modules: session.user.active_modules,
      }
    : null;

  useEffect(() => {
    if (status === 'loading') return;

    const sessionError = (session as any)?.error;
    if (sessionError === 'RefreshAccessTokenError') {
      import('@/lib/auth-refresh').then(({ clearAccessToken }) => clearAccessToken());
      signOut({ redirect: false }).then(() => {
        window.location.href = '/login';
      });
      return;
    }

    if (status === 'authenticated') {
      if (session?.accessToken) {
        import('@/lib/auth-refresh').then(({ setAccessToken }) => {
          setAccessToken(session.accessToken as string);
        });
        setIsAuthReady(true);
      } else if (!hasTriedUpdate) {
        setHasTriedUpdate(true);
        update();
      } else {
        setIsAuthReady(true);
      }
    } else if (status === 'unauthenticated') {
      import('@/lib/auth-refresh').then(({ clearAccessToken }) => clearAccessToken());
      setIsAuthReady(true);
    }
  }, [status, session?.accessToken, (session as any)?.error, hasTriedUpdate]);

  const login = async (email: string, password: string) => {
    const result = await signIn('credentials', {
      email,
      password,
      redirect: false,
    });
    if (result?.error) {
      throw new Error('Ungültige Zugangsdaten');
    }
  };

  const register = async (data: RegisterData) => {
    const res = await fetch(`${API_BASE}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'include',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Registrierung fehlgeschlagen');
    }
    await signIn('credentials', {
      email: data.email,
      password: data.password,
      redirect: false,
    });
  };

  const logout = async () => {
    const { clearAccessToken } = await import('@/lib/auth-refresh');
    clearAccessToken();
    await signOut({ redirect: false });
    window.location.href = '/login';
  };

  const markOnboardingCompleted = async () => {
    await update({ onboarding_completed: true });
  };

  const refreshUser = async () => {
    await update();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken: session?.accessToken ?? null,
        isAuthReady,
        login,
        register,
        logout,
        markOnboardingCompleted,
        refreshUser,
        isAuthenticated,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      accessToken: null,
      isAuthReady: false,
      login: async () => {},
      register: async () => {},
      logout: async () => {},
      markOnboardingCompleted: () => {},
      refreshUser: async () => {},
      isAuthenticated: false,
      isLoading: true,
    } as AuthContextType;
  }
  return context;
};
