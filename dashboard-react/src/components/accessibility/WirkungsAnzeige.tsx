'use client';

import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, Clock, Eye, Loader2, RefreshCw } from 'lucide-react';
import { getApiClient, LANGLAEUFER_TIMEOUT_MS } from '@/lib/api-client';
import { getTrackedWebsites, type TrackedWebsite } from '@/lib/api';
import { generateSiteId } from '@/lib/siteIdUtils';

/**
 * Kommt an, was freigegeben wurde? Die Auslieferung, nachgemessen beim Besucher.
 *
 * Der Wirkungsscan (POST /api/wirkungsscan) misst dieselbe Seite zweimal: einmal
 * ohne complyo-Widget, einmal so, wie ein Besucher sie lädt. Die Anzeige hier
 * hält zwei Fragen auseinander, die leicht verwechselt werden:
 *
 *   Bewertung     Wie steht die Website da?            "ohne complyo", die Hauptzahl
 *   Auslieferung  Was findet der Besucher heute vor?   "mit complyo", die Nebenzahl
 *
 * Die Bewertung hängt an der Website, nicht an einem Skript, das complyo zur
 * Laufzeit einspielt. Wer complyo kündigt, fällt auf den Stand "ohne" zurück.
 * Die Auslieferungszahl darf deshalb nie allein stehen und nie die Hauptzahl
 * sein: eine Zahl, die aus der eigenen Reparatur entsteht, wäre eine Aussage
 * über complyo und keine über die Website des Kunden. Gesperrt ist das durch
 * backend/tests/test_wirkungsanzeige.py.
 *
 * Die Auslieferungszahl erscheint außerdem nur, wenn die Messung beobachtet hat,
 * dass das Skript im zweiten Lauf angefordert wurde (`widget_geladen`). Ohne
 * diese Beobachtung ist jeder Unterschied Messrauschen zweier verschieden
 * geladener Seiten.
 */

type Zuschreibung = boolean | null;

interface Verlaufszeile {
  ohne_widget: number;
  // Fehlen, wenn das Widget nicht beobachtet wurde: die Zahl reist nie ohne ihre Zuschreibung.
  mit_widget?: number;
  behoben?: number;
  widget_geladen: Zuschreibung;
  lage: string;
  gemessen_am: string;
}

interface VerlaufAntwort {
  success: boolean;
  site_id: string;
  messungen: Verlaufszeile[];
}

interface Messergebnis {
  success: boolean;
  gemessen_am: string;
  widget_geladen: boolean;
  ohne_widget: { gesamt: number };
  mit_widget: { gesamt: number };
  urteil: { lage: string; satz: string };
}

const LAGE_TEXT: Record<string, string> = {
  kein_widget: 'complyo nicht eingebaut',
  wirksam: 'wirksam',
  vollstaendig: 'vollständig behoben',
  wirkungslos: 'ohne Wirkung',
  verschlechterung: 'neue Befunde mit complyo',
  unbekannt: 'vor der Widget-Beobachtung gemessen',
};

function fehlertext(err: unknown): string {
  const e = err as { code?: string; response?: { status?: number; data?: { detail?: unknown } } };
  const status = e?.response?.status;
  if (e?.code === 'ECONNABORTED') {
    return 'Die Messung dauert länger als erwartet. Bitte laden Sie die Seite in einer Minute neu: das Ergebnis erscheint dann im Verlauf.';
  }
  if (status === 401) return 'Ihre Sitzung ist abgelaufen. Bitte melden Sie sich erneut an.';
  if (status === 429) return 'Sie haben in der letzten Stunde zehn Messungen ausgelöst. Bitte versuchen Sie es später noch einmal.';
  const detail = e?.response?.data?.detail;
  if (typeof detail === 'string' && detail) return detail;
  return 'Die Messung hat nicht geklappt. Bitte versuchen Sie es später noch einmal.';
}

function domainVon(url: string): string {
  return url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/.*$/, '');
}

function Befunde({ n }: { n: number }) {
  return <>{n === 1 ? '1 Befund' : `${n} Befunde`}</>;
}

/** Die juengste Messung: Bewertung vorn, Auslieferung nur mit Zuschreibung. */
function LetzteMessung({ z }: { z: Verlaufszeile }) {
  const lageText = LAGE_TEXT[z.lage] ?? z.lage;
  return (
    <div className="mt-3 rounded-lg border border-gray-200 p-4 dark:border-zinc-800">
      <p className="text-xs text-gray-500 dark:text-zinc-500">Letzte Messung: {z.gemessen_am}</p>
      <dl className="mt-2 grid gap-4 sm:grid-cols-2">
        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-zinc-500">
            Bewertung Ihrer Website
          </dt>
          <dd className="mt-1 text-2xl font-semibold text-gray-900 dark:text-zinc-100">
            <Befunde n={z.ohne_widget} />
          </dd>
          <dd className="text-xs text-gray-600 dark:text-zinc-400">
            gemessen ohne complyo-Widget. Das ist der Stand Ihrer Website selbst.
          </dd>
        </div>

        <div>
          <dt className="text-xs font-medium uppercase tracking-wide text-gray-500 dark:text-zinc-500">
            Was Besucher heute vorfinden
          </dt>
          {z.widget_geladen === true && z.mit_widget !== undefined ? (
            <>
              <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-zinc-100">
                <Befunde n={z.mit_widget} />
                {z.behoben ? `, ${z.behoben} durch das Widget behoben` : ''}
              </dd>
              <dd className="text-xs text-gray-600 dark:text-zinc-400">
                gemessen mit eingebundenem Widget. Gilt nur, solange das Widget eingebunden bleibt.
              </dd>
            </>
          ) : z.widget_geladen === false ? (
            <dd className="mt-1 text-sm text-amber-800 dark:text-amber-300">
              complyo ist auf dieser Website nicht eingebunden. Es gibt keine Auslieferungszahl,
              Unterschiede zwischen den beiden Läufen sind Messrauschen.
            </dd>
          ) : (
            <dd className="mt-1 text-sm text-gray-600 dark:text-zinc-400">
              Diese Messung stammt aus der Zeit vor der Beobachtung des Widgets. Eine
              Auslieferungszahl lässt sich daraus nicht belegen. Messen Sie neu.
            </dd>
          )}
        </div>
      </dl>
      <p className="mt-3 text-xs text-gray-500 dark:text-zinc-500">Einordnung: {lageText}</p>
    </div>
  );
}

function VerlaufsTabelle({ zeilen }: { zeilen: Verlaufszeile[] }) {
  if (zeilen.length < 2) return null;
  return (
    <div className="mt-3 overflow-x-auto">
      <table className="w-full text-left text-sm">
        <caption className="sr-only">Bisherige Messungen dieser Website</caption>
        <thead>
          <tr className="border-b border-gray-200 text-xs uppercase tracking-wide text-gray-500 dark:border-zinc-800 dark:text-zinc-500">
            <th scope="col" className="py-1.5 pr-4 font-medium">Gemessen</th>
            <th scope="col" className="py-1.5 pr-4 font-medium">Bewertung</th>
            <th scope="col" className="py-1.5 pr-4 font-medium">Beim Besucher</th>
            <th scope="col" className="py-1.5 font-medium">Einordnung</th>
          </tr>
        </thead>
        <tbody>
          {zeilen.map((z, i) => (
            <tr key={`${z.gemessen_am}-${i}`} className="border-b border-gray-100 dark:border-zinc-800/60">
              <td className="py-1.5 pr-4 text-gray-700 dark:text-zinc-300">{z.gemessen_am}</td>
              <td className="py-1.5 pr-4 text-gray-900 dark:text-zinc-100">{z.ohne_widget}</td>
              <td className="py-1.5 pr-4 text-gray-900 dark:text-zinc-100">
                {z.widget_geladen === true && z.mit_widget !== undefined ? z.mit_widget : 'nicht belegt'}
              </td>
              <td className="py-1.5 text-gray-700 dark:text-zinc-300">{LAGE_TEXT[z.lage] ?? z.lage}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function WebsiteZeile({ w }: { w: TrackedWebsite }) {
  const siteId = generateSiteId(w.url);
  const queryClient = useQueryClient();
  const [frisch, setFrisch] = useState<Messergebnis | null>(null);

  const verlauf = useQuery<VerlaufAntwort>({
    queryKey: ['wirkungsscan-verlauf', siteId],
    queryFn: async () =>
      (await getApiClient().get<VerlaufAntwort>(`/api/wirkungsscan/${encodeURIComponent(siteId)}/verlauf`)).data,
    staleTime: 60_000,
    retry: 1,
  });

  const messen = useMutation<Messergebnis, unknown>({
    mutationFn: async () =>
      (await getApiClient().post<Messergebnis>('/api/wirkungsscan', { url: w.url }, { timeout: LANGLAEUFER_TIMEOUT_MS })).data,
    onSuccess: (ergebnis) => {
      setFrisch(ergebnis);
      queryClient.invalidateQueries({ queryKey: ['wirkungsscan-verlauf', siteId] });
    },
  });

  const zeilen = verlauf.data?.messungen ?? [];
  const juengste = zeilen[0];

  return (
    <li className="rounded-lg border border-gray-200 p-4 dark:border-zinc-800">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="font-medium text-gray-900 dark:text-zinc-100">{domainVon(w.url)}</p>
          {!juengste && !verlauf.isLoading && (
            <p className="mt-0.5 flex items-center gap-1.5 text-sm text-amber-700 dark:text-amber-400">
              <Clock className="h-4 w-4" aria-hidden />
              Noch keine Messung
            </p>
          )}
        </div>
        <button
          type="button"
          onClick={() => messen.mutate()}
          disabled={messen.isPending}
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 disabled:cursor-not-allowed disabled:opacity-60 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-200 dark:hover:bg-zinc-700 dark:focus:ring-offset-zinc-900"
        >
          {messen.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
          ) : (
            <RefreshCw className="h-4 w-4" aria-hidden />
          )}
          {messen.isPending ? 'Wird gemessen …' : 'Jetzt messen'}
        </button>
      </div>

      <div aria-live="polite">
        {messen.isPending && (
          <p role="status" className="mt-3 text-sm text-gray-600 dark:text-zinc-400">
            Die Seite wird zweimal im Browser geladen, einmal ohne und einmal mit Widget. Das dauert
            ein bis zwei Minuten.
          </p>
        )}
        {messen.isError && (
          <p role="alert" className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden />
            <span>{fehlertext(messen.error)}</span>
          </p>
        )}
        {frisch && !messen.isPending && (
          <p role="status" className="mt-3 text-sm text-gray-800 dark:text-zinc-200">
            {frisch.urteil.satz}
          </p>
        )}
      </div>

      {verlauf.isError && (
        <p role="alert" className="mt-3 text-sm text-red-800 dark:text-red-300">
          Der Verlauf konnte nicht geladen werden.
        </p>
      )}
      {juengste && <LetzteMessung z={juengste} />}
      <VerlaufsTabelle zeilen={zeilen} />
    </li>
  );
}

export default function WirkungsAnzeige() {
  const { data, isLoading, isError } = useQuery<TrackedWebsite[]>({
    queryKey: ['wirkungsanzeige-websites'],
    queryFn: () => getTrackedWebsites(),
    staleTime: 5 * 60_000,
    retry: 1,
  });

  return (
    <section
      aria-labelledby="wirkung-titel"
      className="max-w-3xl mx-auto mb-6 rounded-xl border border-gray-200 bg-white p-6 shadow dark:border-zinc-800 dark:bg-zinc-900"
    >
      <h2 id="wirkung-titel" className="flex items-center gap-2 text-lg font-semibold text-gray-900 dark:text-zinc-100">
        <Eye className="h-5 w-5 text-teal-600 dark:text-teal-400" aria-hidden />
        Kommt es beim Besucher an?
      </h2>
      <p className="mt-2 text-sm text-gray-600 dark:text-zinc-400">
        Ihre Bewertung hängt an Ihrer Website selbst, nicht an unserem Widget. Deshalb messen wir
        sie ohne Widget. Zusätzlich laden wir die Seite so, wie ein Besucher sie sieht, und
        zeigen, was das Widget davon behebt. Diese zweite Zahl gilt nur, solange das Widget
        eingebunden bleibt, und sie ersetzt keine Reparatur an der Website.
      </p>

      <div className="mt-4">
        {isLoading && (
          <p className="flex items-center gap-2 text-sm text-gray-600 dark:text-zinc-400" role="status">
            <Loader2 className="h-4 w-4 animate-spin" aria-hidden />
            Websites werden geladen …
          </p>
        )}
        {isError && (
          <p role="alert" className="flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" aria-hidden />
            <span>Ihre Websites konnten nicht geladen werden.</span>
          </p>
        )}
        {data && data.length === 0 && (
          <p className="text-sm text-gray-600 dark:text-zinc-400">
            Sie haben noch keine Website hinterlegt. Fügen Sie eine unter „Websites“ hinzu, dann
            können Sie hier messen.
          </p>
        )}
        {data && data.length > 0 && (
          <ul className="space-y-3">
            {data.map((w) => (
              <WebsiteZeile key={w.id} w={w} />
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
