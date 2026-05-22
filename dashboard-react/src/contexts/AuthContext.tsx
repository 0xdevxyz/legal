'use client';

import { createContext, useContext, ReactNode } from 'react';
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
  login: (email: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => void;
  markOnboardingCompleted: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { data: session, status, update } = useSession();

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
    const result = await res.json();
    await signIn('credentials', {
      email: data.email,
      password: data.password,
      redirect: false,
    });
  };

  const logout = async () => {
    await signOut({ redirect: false });
    window.location.href = '/login';
  };

  const markOnboardingCompleted = async () => {
    await update({ onboarding_completed: true });
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        accessToken: session?.accessToken ?? null,
        login,
        register,
        logout,
        markOnboardingCompleted,
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
      login: async () => {},
      register: async () => {},
      logout: () => {},
      markOnboardingCompleted: () => {},
      isAuthenticated: false,
      isLoading: true,
    } as AuthContextType;
  }
  return context;
};
