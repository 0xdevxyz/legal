'use client';

/**
 * Abmahnung prüfen.
 *
 * Der Tag, an dem ein kleines Unternehmen wirklich nach complyo sucht, ist
 * der Tag, an dem eine Abmahnung kommt. Diese Seite nimmt das Schreiben
 * (PDF oder Text), lässt die gewählte Website frisch messen und legt jeden
 * Vorwurf neben die Befunde: bestätigt, nicht gefunden, nicht prüfbar.
 *
 * Messung, keine Rechtsberatung. Die Hinweise (Frist, Anwalt, nicht
 * ignorieren) kommen aus dem Backend und stehen deutlich sichtbar oben,
 * nicht im Kleingedruckten.
 */

import React, { useMemo, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getApiClient } from '@/lib/api-client';
import { analyzeWebsite, getTrackedWebsites } from '@/lib/api';
import ScanProgressPanel from '@/components/dashboard/ScanProgressPanel';
import {
  ShieldAlert, Loader2, AlertTriangle, CheckCircle2, HelpCircle, MinusCircle,
  ExternalLink, ChevronDown, ChevronUp, FileText, Upload,
} from 'lucide-react';

const api = getApiClient();

type Status = 'bestaetigt' | 'nicht_gefunden' | 'nicht_pruefbar' | 'ohne_messung';

interface Befund {
  title: string;
  severity: 'critical' | 'warning' | 'info' | string;
  legal_basis: string;
  category: string;
}

interface Vorwurf {
  vorwurf: string;
  rechtsgrundlage: string | null;
  kategorie: string;
  forderung_euro: number | null;
  frist: string | null;
  status: Status;
  befunde: Befund[];
  hinweis: string;
}

interface Ergebnis {
  website_url: string;
  site_id: string;
  quelle: 'ki' | 'heuristik';
  gemessen_am: string | null;
  mit_messung: boolean;
  vorwuerfe: Vorwurf[];
  zusammenfassung: {
    anzahl: number;
    je_status: Record<Status, number>;
    forderung_summe_euro: number;
    betraege_im_schreiben: number[];
  };
  beleg_url: string | null;
  hinweise: string[];
  disclaimer: string;
}

const STATUS_META: Record<Status, { label: string; icon: React.ElementType; cls: string; badge: string; zahl: string }> = {
  bestaetigt: {
    label: 'Laut Messung nachvollziehbar', icon: AlertTriangle,
    cls: 'border-red-300 bg-red-50', badge: 'bg-red-100 text-red-800', zahl: 'text-red-600',
  },
  nicht_gefunden: {
    label: 'In der Messung nicht gefunden', icon: CheckCircle2,
    cls: 'border-green-300 bg-green-50', badge: 'bg-green-100 text-green-800', zahl: 'text-green-600',
  },
  nicht_pruefbar: {
    label: 'Nicht prüfbar', icon: HelpCircle,
    cls: 'border-amber-300 bg-amber-50', badge: 'bg-amber-100 text-amber-800', zahl: 'text-amber-600',
  },
  ohne_messung: {
    label: 'Ohne Messung', icon: MinusCircle,
    cls: 'border-gray-200 bg-white', badge: 'bg-gray-100 text-gray-600', zahl: 'text-gray-500',
  },
};

const STATUS_REIHENFOLGE: Status[] = ['bestaetigt', 'nicht_gefunden', 'nicht_pruefbar', 'ohne_messung'];

const KATEGORIE_LABEL: Record<string, string> = {
  cookies: 'Cookies & Tracking',
  datenschutz: 'Datenschutz',
  impressum: 'Impressum',
  agb_widerruf: 'AGB & Widerruf',
  barrierefreiheit: 'Barrierefreiheit',
  werbung_uwg: 'Werbung & UWG',
  urheberrecht: 'Urheberrecht',
  sonstiges: 'Sonstiges',
};

const SEVERITY_BADGE: Record<string, string> = {
  critical: 'bg-red-100 text-red-800',
  warning: 'bg-amber-100 text-amber-800',
  info: 'bg-blue-100 text-blue-800',
};

const euro = (n: number) => `${n.toLocaleString('de-DE', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

const datum = (iso: string | null) => {
  if (!iso) return null;
  const d = new Date(iso);
  return isNaN(d.getTime()) ? iso : d.toLocaleString('de-DE');
};

// Fehlercodes der Route in Sätze übersetzen. Die Route liefert selbst schon
// deutsche `detail`-Texte; die Karte hier fängt nur die Fälle ab, in denen
// keiner ankommt (Netz weg, Proxy-Antwort ohne JSON).
const fehlerText = (e: any): string => {
  const status: number | undefined = e?.response?.status;
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  switch (status) {
    case 401: return 'Ihre Sitzung ist abgelaufen. Bitte neu anmelden.';
    case 403: return 'Diese Website ist nicht in Ihrem Konto hinterlegt.';
    case 413: return 'Datei oder Text sind zu groß (PDF bis 10 MB, Text bis 60.000 Zeichen).';
    case 429: return 'Zu viele Prüfungen in kurzer Zeit. Bitte in einer Stunde erneut versuchen.';
    case 503: return 'PDF-Auswertung nicht verfügbar, bitte den Text einfügen.';
    default: return e?.message || 'Die Prüfung ist fehlgeschlagen. Bitte erneut versuchen.';
  }
};

export default function AbmahnungPage() {
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [text, setText] = useState('');
  const [datei, setDatei] = useState<File | null>(null);
  const [phase, setPhase] = useState<'idle' | 'scan' | 'pruefung'>('idle');
  const [scanToken, setScanToken] = useState<string | null>(null);
  const [fehler, setFehler] = useState<string | null>(null);
  const [ergebnis, setErgebnis] = useState<Ergebnis | null>(null);
  const [offen, setOffen] = useState<Record<number, boolean>>({});
  const dateiRef = useRef<HTMLInputElement>(null);

  const websitesQuery = useQuery({
    queryKey: ['tracked-websites'],
    queryFn: () => getTrackedWebsites(),
  });

  const websites = websitesQuery.data ?? [];
  const gewaehlt = websiteUrl || websites.find((w) => w.is_primary)?.url || websites[0]?.url || '';

  const eingabeFehlt = !datei && text.trim().length < 20;
  const laeuft = phase !== 'idle';

  const dateiWaehlen = (f: File | null) => {
    setFehler(null);
    if (!f) { setDatei(null); return; }
    if (f.type !== 'application/pdf') { setFehler('Nur PDF-Dateien werden angenommen.'); return; }
    if (f.size > 10 * 1024 * 1024) { setFehler('Die PDF-Datei ist größer als 10 MB.'); return; }
    setDatei(f);
  };

  const pruefen = async () => {
    if (!gewaehlt || eingabeFehlt || laeuft) return;
    setFehler(null);
    setErgebnis(null);
    setOffen({});

    // Erst messen, dann vergleichen. Ohne frische Messung wäre die Zuordnung
    // eine Erinnerung an einen alten Stand, und die Abmahnung bezieht sich
    // auf heute.
    const merker: { kennung: string | null } = { kennung: null };
    setPhase('scan');
    setScanToken(null);
    try {
      await analyzeWebsite(gewaehlt, undefined, undefined, (k) => {
        merker.kennung = k;
        setScanToken(k);
      });
    } catch (e: any) {
      // Der Scan ist die Grundlage, aber nicht die Bedingung: ohne Messung
      // bekommt der Kunde trotzdem die Vorwurfsliste, mit Status "ohne
      // Messung" und dem Hinweis, den Scan nachzuholen.
      console.warn('Scan vor der Abmahnungsprüfung fehlgeschlagen:', e?.message);
      merker.kennung = null;
    }

    setPhase('pruefung');
    try {
      const form = new FormData();
      form.append('website_url', gewaehlt);
      if (text.trim()) form.append('text', text.trim());
      if (datei) form.append('datei', datei, datei.name);
      if (merker.kennung) form.append('kennung', merker.kennung);
      const res = await api.post<Ergebnis>('/api/abmahnung/pruefen', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000,
      });
      setErgebnis(res.data);
    } catch (e: any) {
      setFehler(fehlerText(e));
    } finally {
      setPhase('idle');
      setScanToken(null);
    }
  };

  const zaehler = useMemo(() => ergebnis?.zusammenfassung.je_status, [ergebnis]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-3 mb-2">
        <ShieldAlert className="w-8 h-8 text-blue-500" />
        <h1 className="text-3xl font-bold">Abmahnung prüfen</h1>
      </div>
      <p className="text-gray-500 mb-6">
        Laden Sie das Schreiben hoch. Wir messen Ihre Website und legen jeden Vorwurf neben
        unseren Befund: stimmt er laut Messung, finden wir nichts dazu, oder können wir ihn
        nicht prüfen. Das ist eine technische Messung und keine Rechtsberatung.
      </p>

      {/* Hinweise, immer sichtbar: die Frist läuft, während man hier liest. */}
      <div className="rounded-2xl border-2 border-amber-300 bg-amber-50 dark:bg-gray-800 dark:border-amber-700 p-5 mb-8">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 mt-0.5 text-amber-600 flex-shrink-0" />
          <div>
            <h2 className="font-bold text-gray-900 dark:text-gray-100 mb-1">Bevor Sie etwas anderes tun</h2>
            <ul className="text-sm text-gray-800 dark:text-gray-200 list-disc pl-5 space-y-1">
              <li>Frist im Schreiben prüfen. Abmahnungen setzen oft nur wenige Tage.</li>
              <li>Nicht ignorieren. Ohne Reaktion folgt meist eine einstweilige Verfügung.</li>
              <li>Unterlassungserklärung nicht ungeprüft unterschreiben. Sie gilt lebenslang.</li>
              <li>Anwältin oder Anwalt einschalten. Dieses Werkzeug ersetzt keine Rechtsberatung.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Eingabe */}
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6 space-y-5 mb-8">
        <div>
          <label className="block text-sm font-medium mb-1" htmlFor="abmahnung-website">Betroffene Website</label>
          {websitesQuery.isLoading ? (
            <div className="flex items-center gap-2 text-sm text-gray-500"><Loader2 className="w-4 h-4 animate-spin" /> Websites werden geladen</div>
          ) : websites.length === 0 ? (
            <p className="text-sm text-red-600">Keine Website im Konto. Bitte zuerst im Dashboard eine Website hinzufügen.</p>
          ) : (
            <select
              id="abmahnung-website"
              className="border rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-900 w-full sm:w-auto"
              value={gewaehlt}
              disabled={laeuft}
              onChange={(e) => setWebsiteUrl(e.target.value)}
            >
              {websites.map((w) => <option key={String(w.id)} value={w.url}>{w.url}</option>)}
            </select>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <span className="block text-sm font-medium mb-1">Schreiben als PDF</span>
            <input
              ref={dateiRef}
              type="file"
              accept="application/pdf"
              className="hidden"
              disabled={laeuft}
              onChange={(e) => dateiWaehlen(e.target.files?.[0] ?? null)}
            />
            <button
              type="button"
              disabled={laeuft}
              onClick={() => dateiRef.current?.click()}
              className="w-full border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-6 text-sm text-gray-600 dark:text-gray-300 hover:border-blue-400 flex flex-col items-center gap-2 disabled:opacity-50"
            >
              {datei ? (
                <>
                  <FileText className="w-6 h-6 text-blue-500" />
                  <span className="font-medium text-gray-900 dark:text-gray-100">{datei.name}</span>
                  <span className="text-xs text-gray-500">{(datei.size / 1024).toFixed(0)} KB, klicken zum Ändern</span>
                </>
              ) : (
                <>
                  <Upload className="w-6 h-6" />
                  <span>PDF auswählen (bis 10 MB, nur Text, keine Bild-Scans)</span>
                </>
              )}
            </button>
            {datei && (
              <button type="button" className="text-xs text-blue-600 mt-1 hover:underline" onClick={() => dateiWaehlen(null)} disabled={laeuft}>
                Datei entfernen
              </button>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium mb-1" htmlFor="abmahnung-text">
              {datei ? 'Ergänzender Text (optional)' : 'Oder: Text des Schreibens einfügen'}
            </label>
            <textarea
              id="abmahnung-text"
              className="border rounded-lg px-3 py-2 text-sm bg-white dark:bg-gray-900 w-full h-40"
              placeholder="Text der Abmahnung hier einfügen"
              value={text}
              maxLength={60000}
              disabled={laeuft}
              onChange={(e) => setText(e.target.value)}
            />
            <p className="text-xs text-gray-500 text-right">{text.length.toLocaleString('de-DE')} / 60.000 Zeichen</p>
          </div>
        </div>

        <p className="text-xs text-gray-500">
          Das Schreiben wird nicht gespeichert. Für die Auswertung wird der Text einmalig an
          den KI-Dienst übermittelt; Namen und Aktenzeichen dürfen Sie vorher schwärzen.
        </p>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={pruefen}
            disabled={laeuft || !gewaehlt || eingabeFehlt}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-semibold disabled:opacity-50 flex items-center gap-2"
          >
            {laeuft && <Loader2 className="w-4 h-4 animate-spin" />}
            {phase === 'scan' ? 'Website wird gemessen' : phase === 'pruefung' ? 'Schreiben wird ausgewertet' : 'Prüfen'}
          </button>
          {eingabeFehlt && !laeuft && (
            <span className="text-xs text-gray-500">PDF hochladen oder mindestens 20 Zeichen Text einfügen.</span>
          )}
        </div>

        {fehler && (
          <div className="rounded-xl border border-red-300 bg-red-50 dark:bg-gray-900 dark:border-red-700 p-4 text-sm text-red-700 dark:text-red-300">
            {fehler}
          </div>
        )}
      </div>

      {phase === 'scan' && (
        <div className="mb-8">
          <ScanProgressPanel url={gewaehlt} token={scanToken} />
        </div>
      )}
      {phase === 'pruefung' && (
        <div className="flex items-center justify-center gap-3 text-gray-500 py-8 mb-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          Vorwürfe werden herausgezogen und mit der Messung verglichen
        </div>
      )}

      {ergebnis && zaehler && (
        <div className="space-y-6">
          {/* Zusammenfassung */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {STATUS_REIHENFOLGE.map((k) => (
              <div key={k} className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4 text-center">
                <div className={`text-3xl font-bold ${STATUS_META[k].zahl}`}>{zaehler[k] ?? 0}</div>
                <div className="text-xs text-gray-500 mt-1">{STATUS_META[k].label}</div>
              </div>
            ))}
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-5 text-sm space-y-2">
            <div className="flex flex-wrap gap-x-6 gap-y-1">
              <span><span className="text-gray-500">Vorwürfe erkannt:</span> <strong>{ergebnis.zusammenfassung.anzahl}</strong></span>
              <span><span className="text-gray-500">Zugeordnete Forderungen:</span> <strong>{euro(ergebnis.zusammenfassung.forderung_summe_euro)}</strong></span>
              {ergebnis.zusammenfassung.betraege_im_schreiben.length > 0 && (
                <span>
                  <span className="text-gray-500">Beträge im Schreiben:</span>{' '}
                  {ergebnis.zusammenfassung.betraege_im_schreiben.map(euro).join(', ')}
                </span>
              )}
            </div>
            <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-gray-500">
              <span>Website: {ergebnis.website_url}</span>
              <span>
                {ergebnis.mit_messung
                  ? `Gemessen am ${datum(ergebnis.gemessen_am) ?? 'unbekannt'}`
                  : 'Ohne Messung: der Scan ist fehlgeschlagen, bitte erneut prüfen.'}
              </span>
              <span>Auswertung: {ergebnis.quelle === 'ki' ? 'KI' : 'Schlüsselwort-Heuristik'}</span>
              {ergebnis.beleg_url && (
                <a href={ergebnis.beleg_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline inline-flex items-center gap-1">
                  Öffentlicher Prüfnachweis <ExternalLink className="w-3 h-3" />
                </a>
              )}
            </div>
          </div>

          {/* Vorwürfe */}
          {ergebnis.vorwuerfe.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <HelpCircle className="w-8 h-8 mx-auto mb-2" />
              Im Text wurden keine Vorwürfe erkannt. Bitte prüfen Sie, ob der eigentliche Vorwurfsteil enthalten ist.
            </div>
          ) : ergebnis.vorwuerfe.map((v, i) => {
            const meta = STATUS_META[v.status] ?? STATUS_META.ohne_messung;
            const Icon = meta.icon;
            const aufgeklappt = !!offen[i];
            return (
              <div key={i} className={`rounded-2xl border-2 p-5 ${meta.cls} dark:bg-gray-800 dark:border-gray-700`}>
                <div className="flex items-start gap-3">
                  <Icon className="w-5 h-5 mt-1 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${meta.badge}`}>{meta.label}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">{KATEGORIE_LABEL[v.kategorie] ?? v.kategorie}</span>
                      {v.forderung_euro != null && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">Forderung {euro(v.forderung_euro)}</span>
                      )}
                      {v.frist && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-800">Frist: {v.frist}</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-900 dark:text-gray-100 mb-1 break-words">{v.vorwurf}</p>
                    {v.rechtsgrundlage && (
                      <p className="text-xs text-gray-500 mb-2">Rechtsgrundlage laut Schreiben: {v.rechtsgrundlage}</p>
                    )}
                    <p className="text-sm text-gray-700 dark:text-gray-300">{v.hinweis}</p>
                    {v.befunde.length > 0 && (
                      <div className="mt-3">
                        <button
                          type="button"
                          onClick={() => setOffen({ ...offen, [i]: !aufgeklappt })}
                          className="text-sm text-blue-600 flex items-center gap-1 hover:underline"
                        >
                          {aufgeklappt ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          {v.befunde.length} passende Befunde {aufgeklappt ? 'ausblenden' : 'anzeigen'}
                        </button>
                        {aufgeklappt && (
                          <ul className="mt-2 space-y-2">
                            {v.befunde.map((b, j) => (
                              <li key={j} className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 p-3 text-sm">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className={`text-xs px-2 py-0.5 rounded-full ${SEVERITY_BADGE[b.severity] ?? 'bg-gray-100 text-gray-600'}`}>{b.severity}</span>
                                  <span className="font-medium text-gray-900 dark:text-gray-100">{b.title}</span>
                                </div>
                                {b.legal_basis && <p className="text-xs text-gray-500 mt-1">{b.legal_basis}</p>}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {/* Hinweise aus dem Backend */}
          <div className="bg-white dark:bg-gray-800 rounded-2xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-bold mb-3">Was jetzt zu tun ist</h2>
            <ol className="list-decimal pl-5 space-y-2 text-sm text-gray-800 dark:text-gray-200">
              {ergebnis.hinweise.map((h, i) => <li key={i}>{h}</li>)}
            </ol>
            <p className="text-xs text-gray-400 mt-4">{ergebnis.disclaimer}</p>
          </div>
        </div>
      )}
    </div>
  );
}
