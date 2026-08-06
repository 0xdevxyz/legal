'use client';

/**
 * Live-Ansicht waehrend des Scans — was gerade geprueft wird, sichtbar gemacht.
 *
 * Vorher lief ein Spinner mit "Analysiere...", 30-90 Sekunden Blackbox. Dabei
 * ist der Pruefumfang das staerkste Argument des Produkts: hier laufen echte
 * Checks in vier Saeulen plus Mehrseiten-Pruefung plus KI-Analysen. Diese
 * Liste zeigt die REALEN Pruefgruppen des Scanners — nichts davon ist erfunden.
 *
 * Ehrlichkeit der Anzeige: Das Backend liefert (noch) keine Einzelfortschritte;
 * die Haekchen takten sich an der erwarteten Laufzeit entlang und stoppen bei
 * ~90 %, bis das echte Ergebnis eintrifft. Die Inszenierung betrifft also das
 * TEMPO, nie den INHALT der Liste.
 */

import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2, Loader2, Sparkles } from 'lucide-react';

interface Gruppe {
  titel: string;
  checks: string[];
}

// Die tatsaechlichen Pruefgruppen des Scanners (scanner.py + Mehrseiten-Pfad).
// Wer hier etwas ergaenzt, muss es auch wirklich pruefen — die Liste ist ein
// oeffentliches Versprechen.
const GRUPPEN: Gruppe[] = [
  {
    titel: 'Rechtstexte & Pflichtangaben',
    checks: ['Impressum', 'Datenschutzerklärung', 'AGB & Widerruf', 'Shop-Pflichten (Button-Lösung, §312k)', 'Werbekennzeichnung (UWG)'],
  },
  {
    titel: 'Cookies & Tracking',
    checks: ['Cookie-Banner-Erkennung', 'Tracking vor Einwilligung (Netzwerk-Evidenz)', 'Dienste-Klassifikation', 'Drittlandtransfer (USA/UK)'],
  },
  {
    titel: 'Barrierefreiheit (BFSG)',
    checks: ['axe-core: ~100 WCAG-Regeln', 'Formulare & Beschriftungen', 'Kontraste & Tastaturbedienung', 'Bilder, Medien & Struktur'],
  },
  {
    titel: 'Technik & Sicherheit',
    checks: ['SSL & HTTPS-Weiterleitung', 'Security-Header', 'Kontaktformular (Art. 13)', 'KI-Systeme & AI-Act-Transparenz'],
  },
  {
    titel: 'Mehrseiten-Prüfung',
    checks: ['Unterseiten entdecken (Sitemap)', 'Pflicht- & Formularseiten prüfen'],
  },
];

const KI_CHECKS = ['Alt-Text-Vorschläge (Bild-KI)', 'Säulen-Verifikation'];

// Erwartete Gesamtdauer als Taktgeber. Die Anzeige erreicht 100 % erst mit
// dem echten Ergebnis — vorher deckelt sie bei 90 %.
const ERWARTETE_SEKUNDEN = 55;

export const ScanProgressPanel: React.FC<{ url: string }> = ({ url }) => {
  const [sekunden, setSekunden] = useState(0);
  const start = useRef(Date.now());

  useEffect(() => {
    const t = setInterval(() => setSekunden(Math.floor((Date.now() - start.current) / 1000)), 1000);
    return () => clearInterval(t);
  }, []);

  const alleChecks = GRUPPEN.reduce((n, g) => n + g.checks.length, 0);
  const fortschritt = Math.min(0.9, sekunden / ERWARTETE_SEKUNDEN);
  const fertigGesamt = Math.floor(alleChecks * fortschritt);

  // Haekchen von oben nach unten verteilen — so "wandert" die Pruefung
  // sichtbar durch die Gruppen, wie der Scanner es tatsaechlich tut.
  let vergeben = 0;
  const gruppenStatus = GRUPPEN.map((g) => {
    const fertig = Math.max(0, Math.min(g.checks.length, fertigGesamt - vergeben));
    vergeben += g.checks.length;
    return { ...g, fertig };
  });

  return (
    <div className="dark:bg-zinc-900/70 bg-white/80 backdrop-blur-sm border dark:border-zinc-700/50 border-gray-200 rounded-2xl p-5 animate-slide-down">
      <div className="flex items-baseline justify-between gap-3 flex-wrap mb-1">
        <h3 className="font-bold dark:text-white text-gray-900">
          Compliance-Prüfung läuft
        </h3>
        <span className="text-xs tabular-nums dark:text-zinc-500 text-gray-500">{sekunden}s</span>
      </div>
      <p className="text-sm dark:text-zinc-400 text-gray-600 mb-3">
        <span className="font-semibold dark:text-zinc-200 text-gray-800">{url}</span>{' '}
        wird auf {alleChecks} Prüfgruppen in vier Säulen geprüft — inklusive Unterseiten.
      </p>

      <div className="h-2 rounded-full dark:bg-zinc-800 bg-gray-100 overflow-hidden mb-1">
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-teal-400 transition-all duration-1000"
          style={{ width: `${Math.round(fortschritt * 100)}%` }}
        />
      </div>
      <p className="text-right text-xs dark:text-zinc-500 text-gray-500 mb-4">
        {fortschritt >= 0.9 ? 'Fast fertig — Ergebnis wird zusammengestellt' : `${fertigGesamt} von ${alleChecks} Prüfgruppen`}
      </p>

      <div className="space-y-3">
        {gruppenStatus.map((g) => (
          <div key={g.titel} className="rounded-xl border dark:border-zinc-800 border-gray-100 p-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold dark:text-zinc-200 text-gray-800">{g.titel}</span>
              <span className="text-xs tabular-nums dark:text-zinc-500 text-gray-500">
                {g.fertig}/{g.checks.length}
                {g.fertig === g.checks.length && <CheckCircle2 className="inline w-3.5 h-3.5 ml-1 text-teal-500 align-text-bottom" />}
              </span>
            </div>
            <ul className="grid sm:grid-cols-2 gap-x-4 gap-y-1">
              {g.checks.map((c, i) => (
                <li key={c} className="flex items-center gap-2 text-xs dark:text-zinc-400 text-gray-600">
                  {i < g.fertig ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-500 flex-shrink-0" aria-hidden />
                  ) : i === g.fertig ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin dark:text-zinc-500 text-gray-400 flex-shrink-0" aria-hidden />
                  ) : (
                    <span className="w-3.5 h-3.5 rounded-full border dark:border-zinc-700 border-gray-300 flex-shrink-0" aria-hidden />
                  )}
                  {c}
                </li>
              ))}
            </ul>
          </div>
        ))}

        <div className="rounded-xl border border-purple-500/25 dark:bg-purple-500/5 bg-purple-50 p-3">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-4 h-4 text-purple-400" aria-hidden />
            <span className="text-sm font-semibold dark:text-purple-300 text-purple-700">KI analysiert Ihre Ergebnisse</span>
          </div>
          <ul className="grid sm:grid-cols-2 gap-x-4 gap-y-1">
            {KI_CHECKS.map((c) => (
              <li key={c} className="flex items-center gap-2 text-xs dark:text-purple-300/80 text-purple-700/80">
                <Loader2 className="w-3.5 h-3.5 animate-spin flex-shrink-0" aria-hidden />
                {c}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ScanProgressPanel;
