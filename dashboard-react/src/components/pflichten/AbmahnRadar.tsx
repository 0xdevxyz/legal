'use client';

/**
 * Abmahn-Radar: bekannte Abmahn- und Bußgeldwellen, verknüpft mit dem eigenen
 * Firmenprofil (Betroffenheit vom Server) und mit den Befunden des aktuellen
 * Scans (Zuordnung hier im Client).
 *
 * Warum die Befund-Zuordnung im Client liegt: die Einzelbefunde eines Scans
 * stehen nicht in der Datenbank, nur die Säulenwerte. Was das Dashboard nach
 * dem Scan im react-query-Cache (Schlüssel 'compliance-analysis' je URL,
 * 'latest-scan') bzw. im Dashboard-Store hält, ist die einzige Quelle. Liegt
 * dort nichts, sagt die Karte das und schickt zum Scan, statt leere Zahlen zu
 * zeigen.
 */
import React, { useMemo, useState } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle, ChevronDown, ExternalLink, Gavel, HelpCircle, Landmark,
  Loader2, Lock, MinusCircle, ShieldAlert,
} from 'lucide-react';
import { getApiClient } from '@/lib/api-client';
import { useDashboardStore, selectAnalysisData } from '@/stores/dashboard';
import type { ComplianceAnalysis, ComplianceIssue } from '@/types/api';

const api = getApiClient();

type Betroffenheit = 'wahrscheinlich' | 'pruefen' | 'unwahrscheinlich' | 'unbekannt';

interface WelleRelevanz {
  rule_status: 'applies' | 'check' | 'not_indicated' | null;
  rule_title: string | null;
  rule_evidence: string[];
  pillar_score: number | null;
  scan_date: string | null;
  scanned_url: string | null;
}

interface Welle {
  id: string;
  titel: string;
  beschreibung: string;
  rule_id: string;
  scan_pillar: 'cookies' | 'gdpr' | 'legal' | 'accessibility' | null;
  stichwoerter: string[];
  art: 'abmahnung' | 'bussgeld' | 'abmahnung_und_bussgeld';
  wer_fordert: string;
  typische_forderung_euro: [number, number] | null;
  forderung_quelle: string;
  seit: string;
  quelle_url: string | null;
  relevanz: WelleRelevanz | null;
  betroffenheit: Betroffenheit | null;
  locked: boolean;
}

interface AbmahnwellenAntwort {
  wellen: Welle[];
  total: number;
  profil_vorhanden: boolean;
  scan_context: { url: string; scan_date: string | null } | null;
  locked: boolean;
  teaser: { hidden_count: number; upgrade_hint: string } | null;
  hinweis: string;
}

/** Ein Befund, wie er aus dem Scan-Cache kommt. Ältere Scans liefern
 *  Befunde teils als bloße Zeichenkette; das Dashboard behandelt beides. */
interface Befund {
  title: string;
  description: string;
  severity: string;
}

const BETROFFENHEIT_META: Record<Betroffenheit, { label: string; badge: string; Icon: React.ComponentType<{ className?: string }> }> = {
  wahrscheinlich: { label: 'Betrifft Sie wahrscheinlich', badge: 'bg-red-100 text-red-800', Icon: AlertTriangle },
  pruefen: { label: 'Bitte prüfen', badge: 'bg-amber-100 text-amber-800', Icon: HelpCircle },
  unwahrscheinlich: { label: 'Laut Profil unwahrscheinlich', badge: 'bg-gray-100 text-gray-600', Icon: MinusCircle },
  unbekannt: { label: 'Ohne Profil nicht einschätzbar', badge: 'bg-gray-100 text-gray-600', Icon: HelpCircle },
};

const ART_META = {
  abmahnung: { label: 'Abmahnung', Icon: Gavel, cls: 'bg-purple-100 text-purple-800' },
  bussgeld: { label: 'Bußgeld (Behörde)', Icon: Landmark, cls: 'bg-blue-100 text-blue-800' },
  abmahnung_und_bussgeld: { label: 'Abmahnung und Bußgeld', Icon: ShieldAlert, cls: 'bg-purple-100 text-purple-800' },
} as const;

const PILLAR_LABEL: Record<string, string> = {
  cookies: 'Cookies',
  gdpr: 'Datenschutz',
  legal: 'Rechtstexte',
  accessibility: 'Barrierefreiheit',
};

const euro = (n: number) => `${n.toLocaleString('de-DE')} €`;

const seitLesbar = (seit: string) => {
  const [jahr, monat] = seit.split('-');
  const d = new Date(Number(jahr), Number(monat) - 1, 1);
  return isNaN(d.getTime()) ? seit : d.toLocaleDateString('de-DE', { month: 'long', year: 'numeric' });
};

function alsBefund(roh: ComplianceIssue | string): Befund {
  if (typeof roh === 'string') return { title: roh, description: '', severity: 'info' };
  return {
    title: roh.title ?? '',
    description: roh.description ?? '',
    severity: roh.severity ?? 'info',
  };
}

/** Sucht im Cache den jüngsten Scan mit Befunden. Reihenfolge nach Zeitstempel,
 *  nicht nach Quelle: der Nutzer soll die Befunde sehen, die er zuletzt gesehen hat. */
function useBefundeAusCache(): { befunde: Befund[]; url: string | null } {
  const queryClient = useQueryClient();
  const storedAnalysis = useDashboardStore(selectAnalysisData);

  return useMemo(() => {
    const kandidaten: Array<ComplianceAnalysis | null | undefined> = [];
    kandidaten.push(queryClient.getQueryData<ComplianceAnalysis | null>(['latest-scan']));
    for (const [, data] of queryClient.getQueriesData<ComplianceAnalysis>({ queryKey: ['compliance-analysis'] })) {
      kandidaten.push(data);
    }
    kandidaten.push(storedAnalysis as ComplianceAnalysis | null);

    const mitBefunden = kandidaten.filter(
      (k): k is ComplianceAnalysis => !!k && Array.isArray(k.issues) && k.issues.length > 0,
    );
    if (mitBefunden.length === 0) return { befunde: [], url: null };
    mitBefunden.sort((a, b) => {
      const ta = Date.parse(a.scan_timestamp ?? '') || 0;
      const tb = Date.parse(b.scan_timestamp ?? '') || 0;
      return tb - ta;
    });
    const scan = mitBefunden[0];
    return {
      befunde: (scan.issues as Array<ComplianceIssue | string>).map(alsBefund),
      url: scan.url ?? null,
    };
  }, [queryClient, storedAnalysis]);
}

function passendeBefunde(welle: Welle, befunde: Befund[]): Befund[] {
  const woerter = welle.stichwoerter.map((s) => s.toLowerCase());
  return befunde.filter((b) => {
    const text = `${b.title} ${b.description}`.toLowerCase();
    return woerter.some((w) => text.includes(w));
  });
}

export default function AbmahnRadar() {
  const [offen, setOffen] = useState<Record<string, boolean>>({});
  const { befunde, url: befundUrl } = useBefundeAusCache();

  const radarQuery = useQuery<AbmahnwellenAntwort>({
    queryKey: ['abmahnwellen'],
    queryFn: async () => (await api.get('/api/pflichten-report/abmahnwellen')).data,
    retry: false,
    staleTime: 10 * 60 * 1000,
  });

  const daten = radarQuery.data;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
      <div className="flex items-center gap-2 mb-1">
        <ShieldAlert className="w-5 h-5 text-red-500" />
        <h2 className="text-lg font-bold">Abmahn-Radar</h2>
      </div>
      <p className="text-xs text-gray-500 mb-4">
        Bekannte Abmahn- und Bußgeldwellen im Website-Recht, verknüpft mit Ihrem Profil und Ihrem letzten Scan.
      </p>

      {radarQuery.isLoading && (
        <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
          <Loader2 className="w-4 h-4 animate-spin" /> Wellen werden geladen
        </div>
      )}
      {radarQuery.isError && (
        <p className="text-sm text-red-600">Abmahn-Radar konnte nicht geladen werden.</p>
      )}

      {daten && (
        <>
          {befunde.length > 0 ? (
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
              Befunde des aktuellen Scans{befundUrl ? ` (${befundUrl})` : ''}: {befunde.length}. Je Welle steht,
              wie viele davon zum Thema passen.
            </p>
          ) : (
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">
              Keine Befunde im Zwischenspeicher.{' '}
              <a href="/" className="text-blue-600 hover:underline">Scan starten</a>, um Befunde zuzuordnen.
            </p>
          )}

          <div className="space-y-3">
            {daten.wellen.map((welle) => {
              const treffer = passendeBefunde(welle, befunde);
              const istOffen = !!offen[welle.id];
              const bMeta = welle.betroffenheit ? BETROFFENHEIT_META[welle.betroffenheit] : null;
              const aMeta = ART_META[welle.art];
              const score = welle.relevanz?.pillar_score ?? null;
              return (
                <div key={welle.id} className="border border-gray-200 dark:border-gray-700 rounded-xl p-4">
                  <button
                    type="button"
                    onClick={() => setOffen({ ...offen, [welle.id]: !istOffen })}
                    className="w-full text-left"
                    aria-expanded={istOffen}
                  >
                    <div className="flex items-start gap-2">
                      <ChevronDown className={`w-4 h-4 mt-1 flex-shrink-0 transition-transform ${istOffen ? 'rotate-180' : ''}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold text-gray-900 dark:text-gray-100">{welle.titel}</span>
                          {welle.locked ? (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 inline-flex items-center gap-1">
                              <Lock className="w-3 h-3" /> Betroffenheit im Pro-Plan
                            </span>
                          ) : bMeta ? (
                            <span className={`text-xs px-2 py-0.5 rounded-full font-semibold inline-flex items-center gap-1 ${bMeta.badge}`}>
                              <bMeta.Icon className="w-3 h-3" /> {bMeta.label}
                            </span>
                          ) : null}
                          <span className={`text-xs px-2 py-0.5 rounded-full inline-flex items-center gap-1 ${aMeta.cls}`}>
                            <aMeta.Icon className="w-3 h-3" /> {aMeta.label}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600 dark:text-gray-400 mt-1">
                          {score !== null && welle.scan_pillar && (
                            <span>
                              Ihre Säule {PILLAR_LABEL[welle.scan_pillar] ?? welle.scan_pillar}:{' '}
                              <span className={score >= 80 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                                {Math.round(score)}/100
                              </span>
                            </span>
                          )}
                          <span>
                            Typische Forderung:{' '}
                            {welle.typische_forderung_euro
                              ? `${euro(welle.typische_forderung_euro[0])} bis ${euro(welle.typische_forderung_euro[1])}`
                              : 'keine belastbare Spanne'}
                          </span>
                          <span>Seit {seitLesbar(welle.seit)}</span>
                          <span className={treffer.length > 0 ? 'text-red-600 font-semibold' : ''}>
                            {befunde.length === 0
                              ? 'Befunde: kein Scan im Zwischenspeicher'
                              : treffer.length === 0
                                ? 'Kein Befund auf Ihrer Website passt dazu'
                                : `${treffer.length} ${treffer.length === 1 ? 'Befund' : 'Befunde'} auf Ihrer Website ${treffer.length === 1 ? 'passt' : 'passen'} dazu`}
                          </span>
                        </div>
                      </div>
                    </div>
                  </button>

                  {istOffen && (
                    <div className="mt-3 ml-6 space-y-2 text-sm text-gray-700 dark:text-gray-300">
                      <p>{welle.beschreibung}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        <span className="font-semibold">Wer fordert:</span> {welle.wer_fordert}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        <span className="font-semibold">Zur Spanne:</span> {welle.forderung_quelle}
                      </p>
                      {welle.relevanz?.rule_title && (
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          <span className="font-semibold">Pflicht laut Profil:</span> {welle.relevanz.rule_title}
                          {welle.relevanz.rule_evidence.length > 0 && ` (Basis: ${welle.relevanz.rule_evidence.join(', ')})`}
                        </p>
                      )}
                      {welle.relevanz?.scanned_url && welle.relevanz.scan_date && (
                        <p className="text-xs text-gray-600 dark:text-gray-400">
                          <span className="font-semibold">Gemessen:</span> {welle.relevanz.scanned_url} am{' '}
                          {new Date(welle.relevanz.scan_date).toLocaleDateString('de-DE')}
                        </p>
                      )}
                      {treffer.length > 0 && (
                        <div>
                          <p className="text-xs font-semibold mb-1">Passende Befunde Ihrer Website:</p>
                          <ul className="list-disc ml-5 text-xs space-y-0.5">
                            {treffer.map((b, i) => (
                              <li key={i}>
                                {b.title}
                                {b.severity === 'critical' && <span className="ml-1 text-red-600">(kritisch)</span>}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {welle.quelle_url && (
                        <a href={welle.quelle_url} target="_blank" rel="noopener noreferrer"
                           className="text-xs text-blue-600 hover:underline inline-flex items-center gap-1">
                          Rechtsgrundlage <ExternalLink className="w-3 h-3" />
                        </a>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {daten.locked && daten.teaser && (
            <p className="text-sm text-blue-700 mt-4 font-medium">
              <Lock className="w-4 h-4 inline mr-1" />
              {daten.teaser.upgrade_hint}{' '}
              <a href="/subscription" className="underline">Jetzt upgraden</a>
            </p>
          )}

          <p className="text-xs text-gray-500 mt-4">{daten.hinweis}</p>
        </>
      )}
    </div>
  );
}
