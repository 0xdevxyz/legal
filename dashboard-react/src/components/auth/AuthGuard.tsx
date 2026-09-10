'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Laesst nur Angemeldete durch.
 *
 * Umgeleitet wird ausschliesslich, wenn feststeht, dass niemand angemeldet
 * ist — nicht, solange die Sitzung laedt. Bis zum 11.09.2026 genuegte
 * "bereit und gerade nicht angemeldet". Der Auth-Kontext gleicht beim Laden
 * einmal den Tarif ab, und next-auth meldet waehrenddessen "laedt". Jeder
 * volle Aufruf einer Unterseite — Lesezeichen, geteilter Link, Neuladen —
 * sprang deshalb auf /login und von dort auf das Dashboard. Ueber die
 * Seitenleiste navigiert fiel es nie auf, weil der Abgleich dann schon
 * gelaufen war.
 *
 * Das Ziel geht jetzt mit: /login?redirect=<Pfad samt Abfrage>. Ohne das
 * landete auch eine wirklich abgelaufene Sitzung nach dem Anmelden auf `/`
 * statt dort, wo der Nutzer gerade war.
 */
export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthReady, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthReady && !isLoading && !isAuthenticated) {
      const ziel = window.location.pathname + window.location.search;
      router.replace(`/login?redirect=${encodeURIComponent(ziel)}`);
    }
  }, [isAuthReady, isLoading, isAuthenticated, router]);

  if (!isAuthReady) {
    return (
      <div className="min-h-screen bg-zinc-950 flex flex-col items-center justify-center gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 border-2 border-orange-400 border-t-transparent rounded-full animate-spin" />
          <span className="text-gray-600 dark:text-zinc-400 text-sm">Wird geladen…</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return <>{children}</>;
}
