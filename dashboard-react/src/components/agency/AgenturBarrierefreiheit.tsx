'use client';

/**
 * Barrierefreiheit über das ganze Portfolio.
 *
 * Das ist die Seite, an der der Agentur-Tarif hängt. Zwanzig Kundenseiten
 * kosten einzeln 20 × 49 € = 980 €; der Agentur-Tarif 299 €. Diese Rechnung
 * geht nur auf, wenn die Arbeit auch wie EIN Vorgang läuft — bisher hieß sie
 * zwanzig Mal aktive Website wechseln, zwanzig Worklists öffnen, zwanzig Mal
 * dieselbe Frage.
 *
 * Was hier bewusst NICHT steht: eine websiteübergreifende Farbfreigabe. Die
 * Messung über 24 echte Kundenseiten ergab 63 Farbpaare, von denen kein
 * einziges auf mehr als einer Website vorkommt — Marken haben eigene Farben.
 * Ein Knopf "alle Farben im Portfolio freigeben" wäre geraten, nicht
 * abgeleitet. Farben bleiben deshalb je Website, aber alle Websites stehen in
 * EINER nach Wirkung sortierten Liste.
 */

import React, { useCallback, useEffect, useState } from 'react';
import {
  Building2, Loader2, RefreshCw, Sparkles, Palette, AlertCircle, Check, ExternalLink,
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface PortfolioSite {
  site_id: string;
  url: string;
  client_name: string;
  alt_texte_offen: number;
  alt_texte_sammelbar: number;
  links_offen: number;
  farben_offen: number;
  farben_freigegeben: number;
  stellen_offen: number;
  offen_gesamt: number;
}

interface KontrastPosten {
  index: number;
  site_id: string;
  url: string;
  client_name: string;
  vordergrund: string;
  hintergrund: string;
  vorschlag: string | null;
  ist_ratio: number;
  neue_ratio: number | null;
  stellen: number;
  loesbar: boolean;
}

interface Portfolio {
  sites: PortfolioSite[];
  kontrast_offen: KontrastPosten[];
  summe: {
    websites: number;
    websites_mit_arbeit: number;
    offen: number;
    stellen: number;
    alt_texte_sammelbar: number;
  };
}

interface Vorschau {
  wird_freigegeben: number;
  auf_websites: number;
  bleibt_zur_pruefung: number;
  wegen_nichtssagend_uebersprungen: number;
  min_konfidenz: number;
  hinweis: string;
}

const LEER: Portfolio = {
  sites: [],
  kontrast_offen: [],
  summe: { websites: 0, websites_mit_arbeit: 0, offen: 0, stellen: 0, alt_texte_sammelbar: 0 },
};

export default function AgenturBarrierefreiheit() {
  const [daten, setDaten] = useState<Portfolio>(LEER);
  const [vorschau, setVorschau] = useState<Vorschau | null>(null);
  const [laedt, setLaedt] = useState(false);
  const [laeuft, setLaeuft] = useState<string | null>(null);
  const [meldung, setMeldung] = useState('');
  const [fehler, setFehler] = useState('');

  const laden = useCallback(async () => {
    setLaedt(true);
    try {
      const [wl, vs] = await Promise.all([
        apiClient.get<Portfolio>('/api/accessibility/agency/worklist'),
        apiClient.get<Vorschau>('/api/accessibility/agency/sammelfreigabe/vorschau'),
      ]);
      setDaten(wl ?? LEER);
      setVorschau(vs ?? null);
      setFehler('');
    } catch {
      setDaten(LEER);
      setFehler('Portfolio konnte nicht geladen werden.');
    } finally {
      setLaedt(false);
    }
  }, []);

  useEffect(() => { laden(); }, [laden]);

  const sammelfreigabe = async () => {
    if (!vorschau?.wird_freigegeben) return;
    if (!window.confirm(
      `${vorschau.wird_freigegeben} Alt-Texte auf ${vorschau.auf_websites} Website(s) ` +
      `freigeben? Sie gehen beim nächsten Abruf des Fix-Manifests live. ` +
      `Jeder einzelne lässt sich später wieder zurückziehen.`
    )) return;
    setLaeuft('sammel');
    setMeldung('');
    try {
      const r = await apiClient.post<{ freigegeben: number; auf_websites: number }>(
        '/api/accessibility/agency/sammelfreigabe', {},
      );
      setMeldung(`${r.freigegeben} Alt-Texte auf ${r.auf_websites} Website(s) freigegeben.`);
      await laden();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFehler(detail || 'Sammelfreigabe fehlgeschlagen.');
    } finally {
      setLaeuft(null);
    }
  };

  const farbenFreigeben = async (site: PortfolioSite) => {
    setLaeuft(site.site_id);
    setMeldung('');
    try {
      const r = await apiClient.post<{ freigegeben: number; stellen: number }>(
        '/api/accessibility/agency/farben-freigeben', { site_id: site.site_id },
      );
      setMeldung(
        `${r.freigegeben} Farbe(n) für ${r.stellen} Fundstellen auf ` +
        `${site.url.replace(/^https?:\/\//, '')} freigegeben.`
      );
      await laden();
    } catch (e: unknown) {
      const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setFehler(detail || 'Freigabe fehlgeschlagen.');
    } finally {
      setLaeuft(null);
    }
  };

  const s = daten.summe;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold dark:text-white text-gray-900 flex items-center gap-2">
            <Building2 className="w-6 h-6 text-purple-400" /> Barrierefreiheit im Portfolio
          </h1>
          <p className="text-sm dark:text-zinc-400 text-gray-600 mt-1">
            {s.websites_mit_arbeit} von {s.websites} Website
            {s.websites === 1 ? '' : 's'} brauchen Arbeit ·{' '}
            <strong>{s.offen} offene Entscheidungen</strong> für {s.stellen} Fundstellen
          </p>
        </div>
        <button
          onClick={laden}
          disabled={laedt}
          className="px-3 py-1.5 text-xs dark:text-white text-gray-800 dark:bg-zinc-700 bg-gray-100 hover:opacity-90 disabled:opacity-40 rounded-lg flex items-center gap-1.5"
        >
          {laedt ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
          Aktualisieren
        </button>
      </div>

      {meldung && (
        <div className="flex items-start gap-2 rounded-xl border border-green-500/30 bg-green-500/10 px-4 py-3">
          <Check className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm dark:text-green-300 text-green-700">{meldung}</p>
        </div>
      )}
      {fehler && (
        <div className="flex items-start gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3">
          <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm dark:text-amber-300 text-amber-700">{fehler}</p>
        </div>
      )}

      {/* Der eine Klick, der über das ganze Portfolio geht. */}
      {vorschau && vorschau.wird_freigegeben > 0 && (
        <section className="rounded-2xl border dark:border-zinc-700 border-gray-200 dark:bg-zinc-900/40 bg-gray-50 p-5">
          <h2 className="flex items-center gap-2 text-sm font-semibold dark:text-zinc-200 text-gray-800">
            <Sparkles className="w-4 h-4 text-blue-400" /> Sammelfreigabe Alt-Texte
          </h2>
          <p className="mt-1.5 text-xs leading-relaxed dark:text-zinc-400 text-gray-600 max-w-3xl">
            <strong>{vorschau.wird_freigegeben} Alt-Texte auf {vorschau.auf_websites} Website
            {vorschau.auf_websites === 1 ? '' : 's'}</strong> stammen von Claude Vision
            (Konfidenz ab {vorschau.min_konfidenz}) — dort hat die KI das Bild
            tatsächlich gesehen. {vorschau.bleibt_zur_pruefung > 0 && (
              <>{vorschau.bleibt_zur_pruefung} Vorschläge aus der Kontext-Heuristik
              bleiben liegen und wollen einzeln angesehen werden.</>
            )}
            {vorschau.wegen_nichtssagend_uebersprungen > 0 && (
              <> {vorschau.wegen_nichtssagend_uebersprungen} wurden als nichtssagend
              aussortiert.</>
            )}
          </p>
          <button
            onClick={sammelfreigabe}
            disabled={laeuft !== null}
            className="mt-4 inline-flex items-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white px-4 py-2.5 text-sm font-semibold disabled:opacity-40"
          >
            {laeuft === 'sammel'
              ? <Loader2 className="w-4 h-4 animate-spin" />
              : <Sparkles className="w-4 h-4" />}
            {vorschau.wird_freigegeben} Alt-Texte freigeben
          </button>
          <p className="mt-3 text-[11px] dark:text-zinc-500 text-gray-500 max-w-3xl">
            {vorschau.hinweis}
          </p>
        </section>
      )}

      {/* Farbentscheidungen — je Website, aber alle Websites in einer Liste. */}
      {daten.kontrast_offen.length > 0 && (
        <section>
          <h2 className="flex items-center gap-2 text-sm font-semibold dark:text-zinc-200 text-gray-800 mb-1">
            <Palette className="w-4 h-4 text-amber-400" /> Offene Farbentscheidungen
            <span className="dark:text-zinc-500 text-gray-500 font-normal">
              (wirkungsvollste zuerst)
            </span>
          </h2>
          <p className="text-xs dark:text-zinc-400 text-gray-600 mb-3 max-w-3xl">
            Farben gehören zur Marke — deshalb je Website und nicht über das
            Portfolio hinweg. Der Gewinn liegt darin, dass Sie dafür nicht
            zwanzig Mal die aktive Website wechseln müssen.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs dark:text-zinc-500 text-gray-500 border-b dark:border-zinc-700 border-gray-200">
                  <th className="py-2 pr-3 font-medium">Website</th>
                  <th className="py-2 pr-3 font-medium">Farbe</th>
                  <th className="py-2 pr-3 font-medium text-right">Stellen</th>
                  <th className="py-2 pr-3 font-medium text-right">jetzt → neu</th>
                </tr>
              </thead>
              <tbody>
                {daten.kontrast_offen.slice(0, 25).map((k) => (
                  <tr key={`${k.site_id}-${k.index}`}
                      className="border-b dark:border-zinc-800 border-gray-100">
                    <td className="py-2 pr-3 dark:text-zinc-300 text-gray-700">
                      {k.client_name && (
                        <span className="dark:text-zinc-500 text-gray-500">{k.client_name} · </span>
                      )}
                      {k.url.replace(/^https?:\/\//, '')}
                    </td>
                    <td className="py-2 pr-3">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="inline-block w-4 h-4 rounded border dark:border-zinc-600 border-gray-300"
                              style={{ backgroundColor: k.vordergrund }} />
                        {k.loesbar && k.vorschlag && (
                          <>
                            <span className="dark:text-zinc-600 text-gray-400">→</span>
                            <span className="inline-block w-4 h-4 rounded border dark:border-zinc-600 border-gray-300"
                                  style={{ backgroundColor: k.vorschlag }} />
                          </>
                        )}
                        {!k.loesbar && (
                          <span className="text-[11px] text-amber-500">nicht lösbar</span>
                        )}
                      </span>
                    </td>
                    <td className="py-2 pr-3 text-right dark:text-zinc-300 text-gray-700 font-medium">
                      {k.stellen}
                    </td>
                    <td className="py-2 pr-3 text-right text-xs dark:text-zinc-400 text-gray-600 font-mono">
                      {k.ist_ratio}:1{k.neue_ratio ? ` → ${k.neue_ratio}:1` : ''}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {daten.kontrast_offen.length > 25 && (
            <p className="mt-2 text-xs dark:text-zinc-500 text-gray-500">
              25 von {daten.kontrast_offen.length} gezeigt.
            </p>
          )}
        </section>
      )}

      {/* Das Portfolio selbst. */}
      <section>
        <h2 className="text-sm font-semibold dark:text-zinc-200 text-gray-800 mb-3">
          Websites
        </h2>
        {daten.sites.length === 0 ? (
          <p className="text-xs dark:text-zinc-500 text-gray-500">
            Noch keine Websites im Konto.
          </p>
        ) : (
          <div className="space-y-2">
            {daten.sites.map((site) => (
              <div
                key={site.site_id}
                className={`rounded-xl border p-4 flex flex-wrap items-center gap-4 ${
                  site.offen_gesamt === 0
                    ? 'border-green-500/25 bg-green-500/5'
                    : 'dark:border-zinc-700 border-gray-200 dark:bg-zinc-900/40 bg-white'
                }`}
              >
                <div className="flex-1 min-w-[14rem]">
                  <div className="flex items-center gap-2 dark:text-zinc-200 text-gray-800 text-sm font-medium">
                    {site.url.replace(/^https?:\/\//, '')}
                    <a href={site.url} target="_blank" rel="noopener noreferrer"
                       aria-label={`${site.url} in neuem Fenster öffnen`}
                       className="dark:text-zinc-500 text-gray-400 hover:opacity-70">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                  {site.client_name && (
                    <div className="text-xs dark:text-zinc-500 text-gray-500 mt-0.5">
                      {site.client_name}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs dark:text-zinc-400 text-gray-600">
                  <span>{site.alt_texte_offen} Alt-Texte</span>
                  <span>{site.links_offen} Links</span>
                  <span>
                    {site.farben_offen} Farben
                    {site.stellen_offen > 0 && (
                      <span className="dark:text-zinc-500 text-gray-500">
                        {' '}({site.stellen_offen} Stellen)
                      </span>
                    )}
                  </span>
                  {site.offen_gesamt === 0 && (
                    <span className="text-green-500 flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" /> nichts offen
                    </span>
                  )}
                </div>

                {site.farben_offen > 0 && (
                  <button
                    onClick={() => farbenFreigeben(site)}
                    disabled={laeuft !== null}
                    className="inline-flex items-center gap-1.5 rounded-lg dark:bg-zinc-700 bg-gray-100 dark:text-zinc-200 text-gray-800 hover:opacity-90 px-3 py-2 text-xs font-semibold disabled:opacity-40"
                  >
                    {laeuft === site.site_id
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      : <Palette className="w-3.5 h-3.5" />}
                    {site.farben_offen} Farbe{site.farben_offen === 1 ? '' : 'n'} freigeben
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
