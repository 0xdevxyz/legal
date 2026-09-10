'use client';

import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
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
  // Nachweis nach Ziffer 1 der AGB (Vertragsschluss nur mit Unternehmern).
  unternehmer_bestaetigt?: boolean;
  agb_version?: string;
  // Fassung des Auftragsverarbeitungsvertrages nach Art. 28 DSGVO, den der
  // Kunde mit der Registrierung in Textform mitschliesst.
  avv_version?: string;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthReady: boolean;
  login: (email: string, password: string, code?: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  markOnboardingCompleted: () => void;
  refreshUser: () => Promise<void>;
  isAuthenticated: boolean;
  isLoading: boolean;
}

/**
 * Das Passwort stimmt, aber das Konto verlangt einen zweiten Faktor.
 *
 * Eine eigene Klasse und keine Fehlermeldung mit Sonderzeichen darin: die
 * Anmeldeseite muss darauf UMSCHALTEN, nicht bloss etwas anzeigen. Auf einen
 * Text zu pruefen waere die Art Bindung, die beim naechsten Umformulieren
 * still zerbricht.
 */
export class ZweiterFaktorNoetig extends Error {
  /** True, wenn schon ein Code eingegeben wurde — dann war dieser falsch. */
  readonly codeWarFalsch: boolean;

  constructor(codeWarFalsch: boolean) {
    super(codeWarFalsch ? 'Der Code stimmt nicht.' : 'Zweiter Faktor erforderlich');
    this.name = 'ZweiterFaktorNoetig';
    this.codeWarFalsch = codeWarFalsch;
  }
}

const AuthContext = createContext<AuthContextType | null>(null);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const { data: session, status, update } = useSession();
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [hasTriedUpdate, setHasTriedUpdate] = useState(false);
  const [hasSyncedPlan, setHasSyncedPlan] = useState(false);

  // Der letzte FESTSTEHENDE Stand der Sitzung.
  //
  // next-auth setzt die Sitzung bei jedem `update()` auf "loading" — auch
  // wenn laengst feststeht, wer angemeldet ist. Dieser Kontext ruft `update()`
  // beim Laden einmal fuer den Tarifabgleich auf (siehe unten). Bis zum
  // 11.09.2026 hiess "loading" hier "nicht angemeldet": die Anmeldewache sah
  // "bereit, aber abgemeldet" und schickte jeden vollen Aufruf einer
  // Unterseite auf /login, und die Anmeldeseite von dort auf das Dashboard.
  //
  // Ein Ref statt State, weil der Wert im selben Render gelten muss, in dem
  // next-auth auf "loading" springt. Mit State kaeme er einen Render zu spaet
  // — genau der Render, in dem die Wache umleitet.
  const bekannterStatus = useRef<'authenticated' | 'unauthenticated' | null>(null);
  if (status !== 'loading') bekannterStatus.current = status;

  // Laedt nur, solange noch nie feststand, wer angemeldet ist.
  const isLoading = status === 'loading' && bekannterStatus.current === null;
  // Eine Aktualisierung im Hintergrund meldet niemanden ab.
  const isAuthenticated =
    status === 'authenticated' ||
    (status === 'loading' && bekannterStatus.current === 'authenticated');

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

  // Plan/Rolle einmal pro Mount frisch aus dem Backend ziehen. Damit erhält ein
  // bereits eingeloggter User mit veraltetem JWT (z. B. nach Stripe-Zahlung) den
  // aktuellen plan_type — auch nach jedem Reload, ohne sich neu einloggen zu müssen.
  useEffect(() => {
    if (isAuthReady && isAuthenticated && session?.accessToken && !hasSyncedPlan) {
      setHasSyncedPlan(true);
      update();
    }
  }, [isAuthReady, isAuthenticated, session?.accessToken, hasSyncedPlan, update]);

  const login = async (email: string, password: string, code?: string) => {
    const result = await signIn('credentials', {
      email,
      password,
      code,
      redirect: false,
    });
    if (!result?.error) return;

    // NextAuth sagt nur "hat nicht geklappt" — `authorize` gibt null zurueck,
    // egal ob das Passwort falsch war oder der zweite Faktor fehlt. Fuer den
    // Nutzer ist das ein gewaltiger Unterschied: einmal muss er das Passwort
    // korrigieren, einmal nur sein Telefon aufschlagen.
    //
    // Deshalb genau hier, nach dem Fehlschlag, eine Rueckfrage beim Backend.
    // Das ist kein Verzeichnis-Orakel: wer bis hierher kommt, hat das richtige
    // Passwort bereits eingegeben.
    try {
      const probe = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      if (probe.ok) {
        const daten = await probe.json();
        if (daten.mfa_required) {
          throw new ZweiterFaktorNoetig(Boolean(code));
        }
      }
    } catch (fehler) {
      if (fehler instanceof ZweiterFaktorNoetig) throw fehler;
      // Netzfehler bei der Rueckfrage: dann eben die allgemeine Meldung.
    }

    throw new Error('Ungültige Zugangsdaten');
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
