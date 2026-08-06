'use client';

/**
 * Live-Ansicht waehrend des Scans — jetzt mit ECHTEM Backend-Fortschritt.
 *
 * Die erste Fassung taktete sich an einer erwarteten Laufzeit entlang; beim
 * ersten echten Scan stand sie bei der Haelfte, als das Ergebnis kam, und die
 * Anzeige sprang um. Eine Anzeige, die nicht stimmt, ist schlimmer als keine.
 *
 * Jetzt melden die Checks selbst (compliance_engine/scan_progress): das Panel
 * pollt den Stand unter einem Client-Token und rendert exakt, was das Backend
 * meldet — inklusive der tatsaechlich entdeckten Unterseiten mit ihren Pfaden.
 */

import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Loader2, Sparkles } from 'lucide-react';
import { apiClient } from '@/lib/api';

interface CheckStand {
  name: string;
  fertig: boolean;
}

interface GruppenStand {
  titel: string;
  checks: CheckStand[];
}

interface Fortschritt {
  phase: string;
  gruppen: GruppenStand[];
  fertig: boolean;
}

const POLL_MS = 1200;

export const ScanProgressPanel: React.FC<{ url: string; token: string | null }> = ({ url, token }) => {
  const [stand, setStand] = useState<Fortschritt | null>(null);
  const [sekunden, setSekunden] = useState(0);
  const start = useRef(Date.now());

  useEffect(() => {
    const uhr = setInterval(
      () => setSekunden(Math.floor((Date.now() - start.current) / 1000)),
      1000,
    );
    return () => clearInterval(uhr);
  }, []);

  useEffect(() => {
    if (!token) return;
    let aktiv = true;
    const poll = async () => {
      try {
        const res = await apiClient.get<Fortschritt>(`/api/v2/analyze-progress/${token}`);
        if (aktiv && res.data) setStand(res.data);
      } catch {
        /* Polling-Fehler sind egal — die Analyse-Antwort beendet das Panel. */
      }
    };
    poll();
    const t = setInterval(poll, POLL_MS);
    return () => {
      aktiv = false;
      clearInterval(t);
    };
  }, [token]);

  const gruppen = stand?.gruppen ?? [];
  const alle = gruppen.reduce((n, g) => n + g.checks.length, 0);
  const fertig = gruppen.reduce((n, g) => n + g.checks.filter((c) => c.fertig).length, 0);
  const prozent = alle > 0 ? Math.round((fertig / alle) * 100) : 0;

  return (
    <div className="dark:bg-zinc-900/70 bg-white/80 backdrop-blur-sm border dark:border-zinc-700/50 border-gray-200 rounded-2xl p-5 animate-slide-down">
      <div className="flex items-baseline justify-between gap-3 flex-wrap mb-1">
        <h3 className="font-bold dark:text-white text-gray-900">Compliance-Prüfung läuft</h3>
        <span className="text-xs tabular-nums dark:text-zinc-500 text-gray-500">{sekunden}s</span>
      </div>
      <p className="text-sm dark:text-zinc-400 text-gray-600 mb-3">
        <span className="font-semibold dark:text-zinc-200 text-gray-800">{url}</span>
        {' — '}
        {stand?.phase ?? 'Scan startet'}
      </p>

      <div className="h-2 rounded-full dark:bg-zinc-800 bg-gray-100 overflow-hidden mb-1">
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-400 transition-all duration-700"
          style={{ width: `${prozent}%` }}
        />
      </div>
      <p className="text-right text-xs dark:text-zinc-500 text-gray-500 mb-4">
        {alle > 0 ? `${fertig} von ${alle} Prüfungen abgeschlossen` : 'Verbinde …'}
      </p>

      <div className="space-y-3">
        {gruppen.map((g) => {
          const istKi = g.titel === 'KI-Analysen';
          const gFertig = g.checks.filter((c) => c.fertig).length;
          return (
            <div
              key={g.titel}
              className={
                istKi
                  ? 'rounded-xl border border-purple-500/25 dark:bg-purple-500/5 bg-purple-50 p-3'
                  : 'rounded-xl border dark:border-zinc-800 border-gray-100 p-3'
              }
            >
              <div className="flex items-center justify-between mb-2">
                <span
                  className={
                    istKi
                      ? 'flex items-center gap-2 text-sm font-semibold dark:text-purple-300 text-purple-700'
                      : 'text-sm font-semibold dark:text-zinc-200 text-gray-800'
                  }
                >
                  {istKi && <Sparkles className="w-4 h-4" aria-hidden />}
                  {g.titel}
                </span>
                <span className="text-xs tabular-nums dark:text-zinc-500 text-gray-500">
                  {gFertig}/{g.checks.length}
                  {gFertig === g.checks.length && (
                    <CheckCircle2 className="inline w-3.5 h-3.5 ml-1 text-teal-500 align-text-bottom" />
                  )}
                </span>
              </div>
              <ul className="grid sm:grid-cols-2 gap-x-4 gap-y-1">
                {g.checks.map((c) => (
                  <li
                    key={c.name}
                    className="flex items-center gap-2 text-xs dark:text-zinc-400 text-gray-600"
                  >
                    {c.fertig ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-500 flex-shrink-0" aria-hidden />
                    ) : (
                      <Loader2
                        className="w-3.5 h-3.5 animate-spin dark:text-zinc-500 text-gray-400 flex-shrink-0"
                        aria-hidden
                      />
                    )}
                    <span className="truncate">{c.name}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        })}

        {gruppen.length === 0 && (
          <div className="flex items-center gap-2 text-sm dark:text-zinc-400 text-gray-600">
            <Loader2 className="w-4 h-4 animate-spin" aria-hidden />
            Prüfumgebung wird vorbereitet …
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanProgressPanel;
