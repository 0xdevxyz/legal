'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Layers, ArrowRight, AlertCircle } from 'lucide-react';
import { getTrackedWebsites, type TrackedWebsite } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

/**
 * Portfolio-Übersicht für Agentur- und Expert-Konten.
 *
 * Wer zwanzig Websites betreut, braucht zuerst die Frage beantwortet "wo
 * brenne ich?" — nicht den Score der einen Seite, die gerade ausgewählt ist.
 * Oben der Durchschnitt über alle geprüften Websites, darunter jede einzeln,
 * die schlechteste zuerst.
 *
 * Ungeprüfte Websites zählen NICHT in den Durchschnitt. Ihr last_score steht
 * in der Datenbank auf 0; sie einzurechnen würde den Schnitt nach unten
 * ziehen und eine Aussage über etwas treffen, das nie gemessen wurde. Sie
 * werden stattdessen separat ausgewiesen.
 */

function farbeFuer(score: number): string {
  if (score <= 40) return '#ef4444';
  if (score <= 60) return '#eab308';
  if (score <= 75) return '#84cc16';
  return '#22c55e';
}

function istGeprueft(w: TrackedWebsite): boolean {
  return (w.scan_count ?? 0) > 0 || !!w.last_scan_date;
}

function anzeigename(w: TrackedWebsite): string {
  return (w.url || '').replace(/^https?:\/\//, '').replace(/\/$/, '');
}

export const AgenturPortfolioKarte: React.FC = () => {
  const router = useRouter();
  const { user } = useAuth();
  const [websites, setWebsites] = useState<TrackedWebsite[] | null>(null);
  const [fehler, setFehler] = useState(false);

  const istAgentur = user?.plan_type === 'agency' || user?.plan_type === 'expert';

  useEffect(() => {
    if (!istAgentur) return;
    let abgebrochen = false;
    getTrackedWebsites()
      .then((liste) => {
        if (!abgebrochen) setWebsites(liste);
      })
      .catch(() => {
        if (!abgebrochen) setFehler(true);
      });
    return () => {
      abgebrochen = true;
    };
  }, [istAgentur]);

  const { geprueft, ungeprueft, schnitt } = useMemo(() => {
    const alle = websites ?? [];
    const g = alle.filter(istGeprueft);
    const u = alle.length - g.length;
    const s = g.length
      ? Math.round(g.reduce((summe, w) => summe + (w.last_score ?? 0), 0) / g.length)
      : null;
    return {
      geprueft: [...g].sort((a, b) => (a.last_score ?? 0) - (b.last_score ?? 0)),
      ungeprueft: u,
      schnitt: s,
    };
  }, [websites]);

  if (!istAgentur) return null;

  return (
    <div className="glass-strong rounded-2xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg" style={{ background: 'var(--lime-dim)' }}>
            <Layers className="w-5 h-5" style={{ color: 'var(--lime)' }} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-gray-900 dark:text-white">Portfolio</h2>
            <p className="text-[11px] text-gray-500 dark:text-zinc-400">
              {websites === null && !fehler
                ? 'wird geladen'
                : `${geprueft.length} geprüft${ungeprueft ? `, ${ungeprueft} offen` : ''}`}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => router.push('/agency')}
          className="text-xs font-semibold inline-flex items-center gap-1 hover:underline"
          style={{ color: 'var(--lime)' }}
        >
          Alle <ArrowRight className="w-3 h-3" aria-hidden="true" />
        </button>
      </div>

      {fehler && (
        <p className="text-xs text-gray-500 dark:text-zinc-400">
          Die Liste konnte nicht geladen werden.
        </p>
      )}

      {websites !== null && geprueft.length === 0 && !fehler && (
        <p className="text-xs text-gray-500 dark:text-zinc-400">
          Noch keine Website geprüft. Der Durchschnitt erscheint nach dem ersten Scan.
        </p>
      )}

      {/* Kumulierter Schnitt */}
      {schnitt !== null && (
        <div className="rounded-xl px-4 py-3 bg-gray-50 dark:bg-white/5">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-black tabular-nums" style={{ color: farbeFuer(schnitt) }}>
              {schnitt}
            </span>
            <span className="text-xs text-gray-500 dark:text-zinc-400">
              Ø über {geprueft.length} {geprueft.length === 1 ? 'Website' : 'Websites'}
            </span>
          </div>
          {ungeprueft > 0 && (
            <p className="mt-1 flex items-center gap-1 text-[11px] text-gray-500 dark:text-zinc-400">
              <AlertCircle className="w-3 h-3 flex-shrink-0" aria-hidden="true" />
              {ungeprueft} noch ungeprüft — nicht im Schnitt
            </p>
          )}
        </div>
      )}

      {/* Einzelne Websites, schlechteste zuerst */}
      {geprueft.length > 0 && (
        <ul className="space-y-1.5 max-h-72 overflow-y-auto pr-1">
          {geprueft.map((w) => {
            const score = w.last_score ?? 0;
            return (
              <li key={String(w.id)}>
                <div className="flex items-center gap-3">
                  <span
                    className="text-sm truncate flex-1 text-gray-700 dark:text-zinc-200"
                    title={anzeigename(w)}
                  >
                    {anzeigename(w)}
                  </span>
                  <span
                    className="text-sm font-bold tabular-nums w-8 text-right"
                    style={{ color: farbeFuer(score) }}
                  >
                    {score}
                  </span>
                </div>
                <div
                  className="mt-1 h-1 rounded-full bg-gray-200 dark:bg-white/10 overflow-hidden"
                  role="img"
                  aria-label={`${anzeigename(w)}: Score ${score} von 100`}
                >
                  <div
                    className="h-full rounded-full"
                    style={{ width: `${Math.max(score, 2)}%`, background: farbeFuer(score) }}
                  />
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};

export default AgenturPortfolioKarte;
