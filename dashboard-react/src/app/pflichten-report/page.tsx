'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api-client';
import {
  Radar, Loader2, AlertTriangle, CheckCircle2, HelpCircle, MinusCircle,
  Lock, ExternalLink, Pencil,
} from 'lucide-react';

const api = getApiClient();

interface ReportItem {
  id: string;
  law: string;
  title: string;
  legal_basis: string;
  deadline: string | null;
  risk_range: [number, number];
  todo: string;
  confidence: number;
  status: 'applies' | 'check' | 'not_indicated';
  evidence: string[];
  why: string;
  scan_status?: { pillar: string; score: number; scanned_url: string };
}

const QUESTIONS: Array<
  | { key: string; label: string; type: 'select'; options: { value: string; label: string }[] }
  | { key: string; label: string; type: 'bool' }
> = [
  {
    key: 'employees', label: 'Wie viele Beschäftigte hat Ihr Unternehmen?', type: 'select',
    options: [
      { value: '1-9', label: '1–9' }, { value: '10-49', label: '10–49' },
      { value: '50-249', label: '50–249' }, { value: '250+', label: '250 oder mehr' },
    ],
  },
  {
    key: 'revenue', label: 'Jahresumsatz (ca.)?', type: 'select',
    options: [
      { value: '<=2m', label: 'bis 2 Mio. €' }, { value: '2-10m', label: '2–10 Mio. €' },
      { value: '10-50m', label: '10–50 Mio. €' }, { value: '>50m', label: 'über 50 Mio. €' },
    ],
  },
  { key: 'b2c', label: 'Richtet sich Ihr Angebot (auch) an Verbraucher (B2C)?', type: 'bool' },
  { key: 'online_shop', label: 'Verkaufen Sie online (Shop / Vertragsabschluss auf der Website)?', type: 'bool' },
  { key: 'digital_service', label: 'Bieten Sie digitale Dienstleistungen an (Buchung, Kundenkonto, App)?', type: 'bool' },
  { key: 'uses_ai_chat', label: 'Setzen Sie einen KI-Chatbot / KI-Assistenten im Kundenkontakt ein?', type: 'bool' },
  { key: 'ai_generated_content', label: 'Veröffentlichen Sie KI-generierte Inhalte (Texte, Bilder, Videos)?', type: 'bool' },
  { key: 'uses_ai_decisions', label: 'Nutzen Sie KI für Entscheidungen über Personen (Bewerbungen, Scoring, Preise)?', type: 'bool' },
  { key: 'sends_b2b_invoices', label: 'Stellen Sie Rechnungen an Unternehmen in Deutschland (B2B)?', type: 'bool' },
  { key: 'sells_connected_products', label: 'Stellen Sie Produkte mit digitalen Elementen her (Software, vernetzte Geräte)?', type: 'bool' },
  { key: 'critical_sector', label: 'Sind Sie in einem NIS2-Sektor tätig (Energie, Gesundheit, Transport, IT-Dienste, Produktion kritischer Güter …)?', type: 'bool' },
  { key: 'newsletter', label: 'Versenden Sie Newsletter / E-Mail-Marketing?', type: 'bool' },
];

const STATUS_META = {
  applies: { label: 'Trifft wahrscheinlich zu', icon: AlertTriangle, cls: 'border-red-300 bg-red-50', badge: 'bg-red-100 text-red-800' },
  check: { label: 'Bitte prüfen', icon: HelpCircle, cls: 'border-amber-300 bg-amber-50', badge: 'bg-amber-100 text-amber-800' },
  not_indicated: { label: 'Keine Indizien', icon: MinusCircle, cls: 'border-gray-200 bg-white', badge: 'bg-gray-100 text-gray-600' },
} as const;

const euro = (n: number) =>
  n >= 1000000 ? `${(n / 1000000).toLocaleString('de-DE')} Mio. €` : `${n.toLocaleString('de-DE')} €`;

export default function PflichtenReportPage() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [answers, setAnswers] = useState<Record<string, any>>({});

  const profileQuery = useQuery({
    queryKey: ['pflichten-profile'],
    queryFn: async () => (await api.get('/api/pflichten-report/profile')).data,
  });

  const reportQuery = useQuery({
    queryKey: ['pflichten-report'],
    queryFn: async () => (await api.get('/api/pflichten-report')).data,
    enabled: profileQuery.data?.exists === true,
    retry: false,
  });

  const updatesQuery = useQuery({
    queryKey: ['pflichten-updates'],
    queryFn: async () => (await api.get('/api/pflichten-report/updates')).data,
    enabled: profileQuery.data?.exists === true,
    retry: false,
  });

  const saveMutation = useMutation({
    mutationFn: async (a: Record<string, any>) =>
      (await api.put('/api/pflichten-report/profile', { answers: a })).data,
    onSuccess: () => {
      setEditing(false);
      queryClient.invalidateQueries({ queryKey: ['pflichten-profile'] });
      queryClient.invalidateQueries({ queryKey: ['pflichten-report'] });
    },
  });

  const startEditing = () => {
    setAnswers(profileQuery.data?.answers ?? {});
    setEditing(true);
  };

  if (profileQuery.isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[50vh]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const showWizard = editing || profileQuery.data?.exists === false;
  const report = reportQuery.data;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <Radar className="w-8 h-8 text-blue-500" />
        <h1 className="text-3xl font-bold">Pflichten-Report</h1>
      </div>
      <p className="text-gray-500 mb-8">
        Welche Regulierungen betreffen Ihr Unternehmen wahrscheinlich — mit Begründung,
        Konfidenz und nächstem Schritt. Selbst-Check auf Basis Ihrer Angaben, keine Rechtsberatung.
      </p>

      {showWizard ? (
        <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 space-y-5">
          <h2 className="text-xl font-semibold">Ihr Firmenprofil ({QUESTIONS.length} Fragen, ~2 Minuten)</h2>
          {QUESTIONS.map((q) => (
            <div key={q.key} className="flex flex-col sm:flex-row sm:items-center gap-2 border-b border-gray-100 dark:border-gray-700 pb-4">
              <span className="flex-1 text-sm">{q.label}</span>
              {q.type === 'select' ? (
                <select
                  className="border rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-900"
                  value={answers[q.key] ?? ''}
                  onChange={(e) => setAnswers({ ...answers, [q.key]: e.target.value })}
                >
                  <option value="" disabled>Bitte wählen</option>
                  {q.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                </select>
              ) : (
                <div className="flex gap-2">
                  {[{ v: true, l: 'Ja' }, { v: false, l: 'Nein' }].map(({ v, l }) => (
                    <button
                      key={l}
                      type="button"
                      onClick={() => setAnswers({ ...answers, [q.key]: v })}
                      className={`px-4 py-2 rounded-lg text-sm border transition ${
                        answers[q.key] === v
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600'
                      }`}
                    >
                      {l}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
          <div className="flex gap-3">
            <button
              onClick={() => saveMutation.mutate(answers)}
              disabled={saveMutation.isPending || !answers.employees || !answers.revenue}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold disabled:opacity-50 flex items-center gap-2"
            >
              {saveMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Report erstellen
            </button>
            {profileQuery.data?.exists && (
              <button onClick={() => setEditing(false)} className="px-6 py-3 rounded-xl border">
                Abbrechen
              </button>
            )}
          </div>
          {saveMutation.isError && (
            <p className="text-sm text-red-600">Speichern fehlgeschlagen — bitte erneut versuchen.</p>
          )}
        </div>
      ) : reportQuery.isLoading ? (
        <div className="flex items-center justify-center min-h-[30vh]">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
        </div>
      ) : report ? (
        <div className="space-y-6">
          {/* Zusammenfassung */}
          <div className="grid grid-cols-3 gap-4">
            {([['applies', 'text-red-600'], ['check', 'text-amber-600'], ['not_indicated', 'text-gray-500']] as const).map(([k, cls]) => (
              <div key={k} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
                <div className={`text-3xl font-bold ${cls}`}>{report.counts[k]}</div>
                <div className="text-xs text-gray-500 mt-1">{STATUS_META[k].label}</div>
              </div>
            ))}
          </div>

          <div className="flex justify-end">
            <button onClick={startEditing} className="text-sm text-blue-600 flex items-center gap-1 hover:underline">
              <Pencil className="w-4 h-4" /> Profil bearbeiten
            </button>
          </div>

          {/* Pflichten-Liste */}
          {report.items.map((item: ReportItem) => {
            const meta = STATUS_META[item.status];
            const Icon = meta.icon;
            return (
              <div key={item.id} className={`rounded-2xl border-2 p-5 ${meta.cls} dark:bg-gray-800 dark:border-gray-700`}>
                <div className="flex items-start gap-3">
                  <Icon className="w-5 h-5 mt-1 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <h3 className="font-bold text-gray-900 dark:text-gray-100">{item.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${meta.badge}`}>{meta.label}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">{item.law}</span>
                      {item.deadline && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">{item.deadline}</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">{item.why}</p>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">→ {item.todo}</p>
                    {item.scan_status && (
                      <p className="text-xs text-gray-600 mb-1">
                        Ist-Zustand laut Website-Scan ({item.scan_status.scanned_url}):{' '}
                        <span className={item.scan_status.score >= 80 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                          Score {Math.round(item.scan_status.score)}/100
                        </span>
                      </p>
                    )}
                    <p className="text-xs text-gray-500">
                      {item.legal_basis} · Risikorahmen {euro(item.risk_range[0])}–{euro(item.risk_range[1])} ·
                      Konfidenz {Math.round(item.confidence * 100)} % · Basis: {item.evidence.join(', ')}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}

          {/* Änderungs-Feed (Phase 7.3 lebender Pflichten-Graph) */}
          {updatesQuery.data && updatesQuery.data.total_events > 0 && (
            <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
              <h2 className="text-lg font-bold mb-1">Aktuelle Entwicklungen zu Ihren Pflichten</h2>
              <p className="text-xs text-gray-500 mb-4">
                Automatisch zugeordnet aus dem Rechts-Monitoring ({updatesQuery.data.total_events} Meldungen)
              </p>
              <div className="space-y-3">
                {updatesQuery.data.events.map((ev: any, idx: number) => (
                  <div key={idx} className="border-l-4 border-blue-400 pl-3 py-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">{ev.rule_title}</span>
                      {ev.published_at && (
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          {new Date(ev.published_at).toLocaleDateString('de-DE')}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-medium mt-1">{ev.title}</p>
                    {ev.summary && <p className="text-xs text-gray-500 line-clamp-2">{ev.summary}</p>}
                    {ev.source_url && (
                      <a href={ev.source_url} target="_blank" rel="noopener noreferrer"
                         className="text-xs text-blue-600 hover:underline inline-flex items-center gap-1">
                        Quelle <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
              {updatesQuery.data.locked && updatesQuery.data.teaser && (
                <p className="text-sm text-blue-700 mt-4 font-medium">
                  <Lock className="w-4 h-4 inline mr-1" />
                  {updatesQuery.data.teaser.upgrade_hint}
                </p>
              )}
            </div>
          )}

          {/* Teaser / Upgrade */}
          {report.locked && report.teaser && (
            <div className="rounded-2xl border-2 border-blue-300 bg-blue-50 dark:bg-gray-800 p-6 text-center">
              <Lock className="w-6 h-6 mx-auto text-blue-500 mb-2" />
              <p className="font-semibold mb-2">{report.teaser.upgrade_hint}</p>
              <a href="/subscription" className="inline-flex items-center gap-1 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold">
                Jetzt upgraden <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          )}

          <p className="text-xs text-gray-600 dark:text-gray-400">{report.disclaimer}</p>
        </div>
      ) : (
        <div className="text-center text-gray-500 py-12">
          <CheckCircle2 className="w-8 h-8 mx-auto mb-2" />
          Report konnte nicht geladen werden — bitte Profil (neu) ausfüllen.
        </div>
      )}
    </div>
  );
}
