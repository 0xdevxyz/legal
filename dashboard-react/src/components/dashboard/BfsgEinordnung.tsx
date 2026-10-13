'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Scale, ChevronDown, ExternalLink, ListChecks } from 'lucide-react';
import type { BfsgEinordnung as BfsgEinordnungDaten, PositiveCheck } from '@/types/api';

/**
 * BFSG-Einordnung über der Säule Barrierefreiheit.
 *
 * Drei Stufen aus backend/compliance_engine/bfsg_einordnung.py:
 *   applies        BFSG greift wahrscheinlich (Betrag und Pflicht am Befund)
 *   check          Einordnung offen (kein Profil, Kleinstunternehmen, Widerspruch)
 *   not_indicated  nach Profil keine BFSG-Pflicht angezeigt (WCAG-Abweichung bleibt)
 *
 * Der Kasten legt die Kriterien neben die Profilwerte, statt zu urteilen.
 * Die Messung ändert sich nicht; die Punkte zählen in jedem Fall voll.
 */

const STUFE: Record<string, { rahmen: string; punkt: string; text: string }> = {
  applies: {
    rahmen: 'border-red-300 dark:border-red-500/40 bg-red-50 dark:bg-red-500/10',
    punkt: 'bg-red-500',
    text: 'text-red-800 dark:text-red-300',
  },
  check: {
    rahmen: 'border-amber-300 dark:border-amber-500/40 bg-amber-50 dark:bg-amber-500/10',
    punkt: 'bg-amber-500',
    text: 'text-amber-800 dark:text-amber-300',
  },
  not_indicated: {
    rahmen: 'border-gray-200 dark:border-zinc-700/60 bg-white dark:bg-zinc-900/60',
    punkt: 'bg-zinc-400',
    text: 'text-gray-800 dark:text-zinc-200',
  },
};

export const BfsgEinordnungKasten: React.FC<{ einordnung?: BfsgEinordnungDaten | null }> = ({ einordnung }) => {
  const [offen, setOffen] = useState(false);
  if (!einordnung) return null;
  const stufe = STUFE[einordnung.status] ?? STUFE.check;

  return (
    <div className={`rounded-xl border p-4 ${stufe.rahmen}`} data-testid="bfsg-einordnung">
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-lg bg-black/5 dark:bg-white/5 flex-shrink-0">
          <Scale className="w-4 h-4 text-gray-700 dark:text-zinc-200" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`inline-block w-2 h-2 rounded-full ${stufe.punkt}`} />
            <span className={`text-sm font-semibold ${stufe.text}`}>{einordnung.label}</span>
          </div>
          <p className="text-sm text-gray-700 dark:text-zinc-300 mt-1 leading-relaxed">{einordnung.text}</p>

          <dl className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1.5 text-xs">
            {einordnung.kriterien.map((k) => (
              <div key={k.schluessel} className="flex items-baseline justify-between gap-3 border-b border-black/5 dark:border-white/5 pb-1">
                <dt className="text-gray-600 dark:text-zinc-400">{k.label}</dt>
                <dd className="font-semibold text-gray-900 dark:text-white text-right">
                  {k.wert ?? <span className="font-normal text-gray-500 dark:text-zinc-500">keine Angabe</span>}
                </dd>
              </div>
            ))}
          </dl>

          {!einordnung.profil_vorhanden && (
            <Link
              href={einordnung.profil_pfad || '/pflichten-report'}
              className="inline-flex items-center gap-1.5 mt-3 text-sm font-semibold text-teal-700 dark:text-teal-300 hover:underline"
            >
              Unternehmensprofil ausfüllen, dann ordnet complyo die Befunde ein
              <ExternalLink className="w-3.5 h-3.5" />
            </Link>
          )}

          <button
            type="button"
            onClick={() => setOffen(!offen)}
            className="mt-3 inline-flex items-center gap-1 text-xs text-gray-600 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-white"
            aria-expanded={offen}
          >
            Begründung und Quelle
            <ChevronDown className={`w-3.5 h-3.5 transition-transform ${offen ? 'rotate-180' : ''}`} />
          </button>
          {offen && (
            <div className="mt-2 text-xs text-gray-600 dark:text-zinc-400 space-y-1.5">
              <ul className="list-disc pl-4 space-y-0.5">
                {einordnung.gruende.map((g, i) => <li key={i}>{g}</li>)}
              </ul>
              <p>Rechtsgrundlage: {einordnung.rechtsgrundlage}</p>
              <p>Quelle: {einordnung.quelle}</p>
              <p className="italic">{einordnung.hinweis}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/**
 * Geprüfte Regeln ohne Abweichung (axe-Messprotokoll).
 *
 * Bis zum 13.10.2026 entstand "N bestanden" aus der Abwesenheit von Befunden.
 * Jetzt steht hier, welche Regel auf wie vielen Seiten lief und wie viele
 * Elemente dabei gemessen wurden. Wortwahl: "keine Abweichung gefunden".
 */
export const GepruefteRegeln: React.FC<{ checks: PositiveCheck[]; standardOffen?: boolean }> = ({ checks, standardOffen = false }) => {
  const [offen, setOffen] = useState(standardOffen);
  const regeln = (checks || []).filter((c) => c && c.status === 'geprueft_ohne_abweichung');
  if (regeln.length === 0) return null;
  const pflicht = regeln.filter((r) => r.rechtspflicht);
  const seitenGesamt = Math.max(...regeln.map((r) => r.seiten_gesamt ?? r.seiten ?? 1));

  return (
    <div className="rounded-xl border border-emerald-200 dark:border-emerald-500/30 bg-emerald-50/60 dark:bg-emerald-500/5" data-testid="geprueft-ohne-abweichung">
      <button
        type="button"
        onClick={() => setOffen(!offen)}
        className="w-full flex items-center justify-between gap-3 p-4 text-left"
        aria-expanded={offen}
      >
        <div className="flex items-center gap-3 min-w-0">
          <div className="p-2 rounded-lg bg-emerald-500/15 flex-shrink-0">
            <ListChecks className="w-4 h-4 text-emerald-700 dark:text-emerald-300" />
          </div>
          <div className="min-w-0">
            <p className="text-sm font-semibold text-gray-900 dark:text-white">
              {regeln.length} Regeln geprüft, keine Abweichung gefunden
            </p>
            <p className="text-xs text-gray-600 dark:text-zinc-400">
              {pflicht.length} WCAG-Regeln und {regeln.length - pflicht.length} Best-Practice-Regeln, gemessen auf {seitenGesamt} {seitenGesamt === 1 ? 'Seite' : 'Seiten'}.
              Eine automatische Prüfung deckt nur einen Teil der WCAG-Kriterien ab.
            </p>
          </div>
        </div>
        <ChevronDown className={`w-4 h-4 text-zinc-400 flex-shrink-0 transition-transform ${offen ? 'rotate-180' : ''}`} />
      </button>
      {offen && (
        <ul className="border-t border-emerald-200/70 dark:border-emerald-500/20 divide-y divide-emerald-200/50 dark:divide-emerald-500/10">
          {regeln.map((r) => (
            <li key={r.id || r.title} className="px-4 py-2.5 flex items-start justify-between gap-3 text-sm">
              <div className="min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-gray-900 dark:text-white">{r.title}</span>
                  {r.wcag && r.wcag.length > 0 && (
                    <span className="text-[11px] px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/10 text-gray-700 dark:text-zinc-300">
                      WCAG {r.wcag.join(', ')}
                    </span>
                  )}
                  {r.rechtspflicht === false && (
                    <span className="text-[11px] px-1.5 py-0.5 rounded bg-black/5 dark:bg-white/10 text-gray-600 dark:text-zinc-400">
                      Best Practice
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 dark:text-zinc-400 mt-0.5">{r.wortlaut}</p>
              </div>
              {r.help_url && (
                <a
                  href={r.help_url}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-xs text-teal-700 dark:text-teal-300 hover:underline flex-shrink-0 inline-flex items-center gap-1"
                  aria-label={`Regel ${r.id || ''} bei Deque öffnen`}
                >
                  Regel <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
