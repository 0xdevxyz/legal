'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertCircle, Check, Clock, Copy, ExternalLink, Loader2, ShieldCheck } from 'lucide-react';
import { getApiClient } from '@/lib/api-client';

/**
 * Der oeffentliche Pruefnachweis, aus Sicht des Kunden.
 *
 * Das Protokoll (/nachweis/{site}/{token}) und die daraus erzeugte
 * Barrierefreiheitserklaerung gab es seit August, ohne Anmeldung abrufbar.
 * Im Dashboard sah der Kunde davon bis zum 11.09.2026 nichts: kein Link,
 * kein Einbettungscode. Diese Karte zeigt je Website, ob es einen Nachweis
 * gibt, und gibt die Adressen und den fertigen Link zum Kopieren.
 */

interface NachweisWebsite {
  website_id: number;
  url: string;
  site_id: string;
  nachweis_vorhanden: boolean;
  gemessen_am: string | null;
  urls: {
    nachweis_json: string;
    nachweis_seite: string;
    erklaerung_seite: string;
    erklaerung_markdown: string;
  };
  einbettung: string;
}

interface NachweisLinksAntwort {
  verfuegbar: boolean;
  grund?: string;
  websites: NachweisWebsite[];
}

function fehlertext(err: unknown): string {
  const e = err as { response?: { status?: number; data?: { detail?: unknown } } };
  const status = e?.response?.status;
  if (status === 401) return 'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.';
  if (status === 403) return 'Für dieses Konto ist der Prüfnachweis nicht freigeschaltet.';
  if (status === 503) return 'Der Prüfnachweis ist gerade nicht erreichbar. Bitte versuchen Sie es in ein paar Minuten noch einmal.';
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  return 'Die Nachweis-Adressen konnten nicht geladen werden.';
}

async function inZwischenablage(text: string): Promise<boolean> {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    /* unten der Ersatzweg */
  }
  try {
    const feld = document.createElement('textarea');
    feld.value = text;
    feld.setAttribute('readonly', '');
    feld.style.position = 'fixed';
    feld.style.left = '-9999px';
    document.body.appendChild(feld);
    feld.select();
    const ok = document.execCommand('copy');
    document.body.removeChild(feld);
    return ok;
  } catch {
    return false;
  }
}

function KopierKnopf({ text, was }: { text: string; was: string }) {
  const [zustand, setZustand] = useState<'bereit' | 'kopiert' | 'fehler'>('bereit');
  const klick = async () => {
    const ok = await inZwischenablage(text);
    setZustand(ok ? 'kopiert' : 'fehler');
    window.setTimeout(() => setZustand('bereit'), 2000);
  };
  return (
    <button
      type="button"
      onClick={klick}
      aria-label={`${was} kopieren`}
      className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-2.5 py-1.5 text-xs font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 dark:focus:ring-offset-zinc-900"
    >
      {zustand === 'kopiert' ? <Check className="h-3.5 w-3.5" aria-hidden /> : <Copy className="h-3.5 w-3.5" aria-hidden />}
      <span aria-live="polite">
        {zustand === 'kopiert' ? 'Kopiert' : zustand === 'fehler' ? 'Bitte markieren und kopieren' : 'Kopieren'}
      </span>
    </button>
  );
}

function LinkZeile({ label, href, was }: { label: string; href: string; was: string }) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-700 underline-offset-2 hover:underline dark:text-blue-400"
      >
        {label}
        <ExternalLink className="h-3.5 w-3.5" aria-hidden />
        <span className="sr-only">(öffnet in neuem Fenster)</span>
      </a>
      <KopierKnopf text={href} was={was} />
    </div>
  );
}

function WebsiteZeile({ w }: { w: NachweisWebsite }) {
  const domain = w.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/.*$/, '');
  return (
    <li className="rounded-lg border border-gray-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="font-medium text-gray-900 dark:text-zinc-100">{domain}</p>
          {w.nachweis_vorhanden ? (
            <p className="mt-0.5 flex items-center gap-1.5 text-sm text-green-700 dark:text-green-400">
              <ShieldCheck className="h-4 w-4" aria-hidden />
              Nachweis vorhanden{w.gemessen_am ? `, Stand ${w.gemessen_am}` : ''}
            </p>
          ) : (
            <p className="mt-0.5 flex items-center gap-1.5 text-sm text-amber-700 dark:text-amber-400">
              <Clock className="h-4 w-4" aria-hidden />
              Noch keine Messung
            </p>
          )}
        </div>
      </div>

      {w.nachweis_vorhanden ? (
        <div className="mt-3 space-y-3">
          <LinkZeile label="Prüfprotokoll ansehen" href={w.urls.nachweis_seite} was="Adresse des Prüfprotokolls" />
          <LinkZeile label="Erklärung zur Barrierefreiheit ansehen" href={w.urls.erklaerung_seite} was="Adresse der Erklärung" />
          <div>
            <p className="mb-1 text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-zinc-500">
              Link für Ihre Website
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <code className="max-w-full overflow-x-auto rounded-md bg-gray-100 px-2 py-1.5 text-xs text-gray-800 dark:bg-zinc-800 dark:text-zinc-200">
                {w.einbettung}
              </code>
              <KopierKnopf text={w.einbettung} was="Einbettungscode" />
            </div>
          </div>
        </div>
      ) : (
        <p className="mt-3 text-sm text-gray-600 dark:text-zinc-400">
          Sobald Sie diese Website auf Barrierefreiheit{' '}
          <a href="/" className="underline text-blue-700 dark:text-blue-400">scannen</a>{' '}
          und Reparaturen{' '}
          <a href="/accessibility/worklist" className="underline text-blue-700 dark:text-blue-400">freigeben</a>,
          entsteht hier der Nachweis. Die Adressen bleiben dabei fest, Sie können sie
          schon jetzt einplanen.
        </p>
      )}
    </li>
  );
}

export default function NachweisLinks() {
  const api = getApiClient();
  const { data, isLoading, isError, error } = useQuery<NachweisLinksAntwort>({
    queryKey: ['nachweis-links'],
    queryFn: async () => (await api.get<NachweisLinksAntwort>('/api/nachweis-links')).data,
    staleTime: 5 * 60_000,
    retry: 1,
  });

  return (
    <section
      aria-labelledby="nachweis-titel"
      className="max-w-3xl mx-auto mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow dark:border-zinc-800 dark:bg-zinc-900"
    >
      <h2 id="nachweis-titel" className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-zinc-100">
        <ShieldCheck className="h-5 w-5 text-teal-600 dark:text-teal-400" aria-hidden />
        Ihr öffentlicher Prüfnachweis
      </h2>
      <p className="mt-2 text-sm text-gray-600 dark:text-zinc-400">
        Für jede geprüfte Website gibt es ein öffentliches Protokoll: was gemessen wurde,
        was repariert ist und was noch offen ist. Daraus entsteht Ihre Erklärung zur
        Barrierefreiheit. Beides braucht keine Anmeldung, Sie können die Adressen
        weitergeben oder auf Ihrer Website verlinken. Die Erklärung aktualisiert sich mit
        jeder Messung von selbst und benennt bekannte Lücken, statt sie zu verschweigen.
      </p>

      <div className="mt-4">
        {isLoading && (
          <p className="flex items-center gap-2 text-sm text-gray-600 dark:text-zinc-400" role="status">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Nachweis-Adressen werden geladen …
          </p>
        )}

        {isError && (
          <p role="alert" className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden />
            <span>{fehlertext(error)}</span>
          </p>
        )}

        {data && !data.verfuegbar && (
          <p role="status" className="flex items-start gap-2 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900 dark:border-amber-500/40 dark:bg-amber-500/10 dark:text-amber-200">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden />
            <span>{data.grund || 'Der öffentliche Prüfnachweis ist derzeit nicht eingerichtet.'}</span>
          </p>
        )}

        {data?.verfuegbar && data.websites.length === 0 && (
          <p className="text-sm text-gray-600 dark:text-zinc-400">
            Sie haben noch keine Website hinterlegt. Sobald Sie eine Website hinzufügen und
            auf Barrierefreiheit scannen, erscheint hier ihr Nachweis.
          </p>
        )}

        {data?.verfuegbar && data.websites.length > 0 && (
          <ul className="space-y-3">
            {data.websites.map((w) => (
              <WebsiteZeile key={w.website_id} w={w} />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
