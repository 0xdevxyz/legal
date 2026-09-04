'use client';

/**
 * Farbentscheidungen freigeben.
 *
 * Hier wird aus einer Messung eine Reparatur. Der Scan findet auf einer
 * typischen Kundenseite rund zehn Kontrastfehler — aber nur drei Farbpaare;
 * dieselbe Kombination wiederholt sich. Deshalb zeigt diese Karte nicht zehn
 * Fehler, sondern drei Entscheidungen, und schreibt an jede, wie viele Stellen
 * daran hängen. Das ist der ganze Unterschied zu einem Report: der Kunde
 * bestätigt drei Farben statt zehn Befunde zu lesen.
 *
 * Zwei Dinge, die die Karte bewusst NICHT tut:
 *
 *  - Sie behauptet keine Verbesserung, die nicht gemessen wurde. Jede
 *    angezeigte Ratio kommt aus der Nachmessung im Browser, nicht aus einer
 *    Formel (siehe kontrast_verifizierer.py).
 *  - Sie nimmt keine eigene Farbe blind an. Wer einen anderen Ton eintippt,
 *    bekommt ihn nur, wenn er die geforderte Ratio erreicht — sonst lehnt der
 *    Endpunkt ab und sagt, warum. Eine Zusage "erfüllt WCAG 2.1 AA" darf nicht
 *    daran scheitern, dass jemand eine hübschere Farbe wollte.
 *
 * Nichts hiervon geht ohne Klick live: der Fix liegt auf 'pending', und das
 * Manifest liefert nur Freigegebenes aus.
 */

import React, { useCallback, useState } from 'react';
import { Palette, Check, X, Loader2, AlertCircle, Pencil, Undo2 } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

/**
 * Kontrastverhaeltnis nach WCAG 2.1 — dieselbe Formel wie im Backend.
 *
 * Sie steht hier, weil die Vorschau sonst luegen wuerde: tippt jemand eine
 * eigene Farbe ein, zeigt das Muster sofort seine Farbe, die Kennzahl daneben
 * waere aber noch die des urspruenglichen Vorschlags. Eine Zahl, die nicht zum
 * Bild passt, ist schlimmer als keine.
 *
 * Verbindlich bleibt die Pruefung im Backend — hier geht es nur darum, dem
 * Nutzer beim Tippen zu zeigen, wohin er steuert.
 */
function ratio(vorn: string, hinten: string): number | null {
  const rgb = (hex: string): [number, number, number] | null => {
    const m = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(hex.trim());
    if (!m) return null;
    const h = m[1].length === 3 ? m[1].split('').map((c) => c + c).join('') : m[1];
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)) as [number, number, number];
  };
  const lum = (c: [number, number, number]) =>
    c.map((v) => {
      const s = v / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    }).reduce((a, v, i) => a + v * [0.2126, 0.7152, 0.0722][i], 0);
  const a = rgb(vorn), b = rgb(hinten);
  if (!a || !b) return null;
  const [hell, dunkel] = [lum(a), lum(b)].sort((x, y) => y - x);
  return Math.round(((hell + 0.05) / (dunkel + 0.05)) * 100) / 100;
}

export interface KontrastEntscheidung {
  index: number;
  vordergrund: string;
  hintergrund: string;
  vorschlag: string | null;
  ist_ratio: number;
  neue_ratio: number | null;
  ziel_ratio: number;
  stellen: number;
  loesbar: boolean;
  bestaetigt?: boolean;
  freigabe: 'pending' | 'approved' | 'rejected';
  hinweis?: string;
  beispiel_html?: string;
}

/** Kleine Vorschau: echte Farbe auf echtem Grund, damit man es sieht statt liest. */
const Probe: React.FC<{ vorn: string; hinten: string; label: string; warnt?: boolean }> = ({
  vorn, hinten, label, warnt = false,
}) => (
  <div className="flex flex-col gap-1">
    <div
      className="rounded-lg border dark:border-zinc-700 border-gray-300 px-3 py-2 text-sm font-medium"
      style={{ backgroundColor: hinten, color: vorn }}
    >
      Beispieltext
    </div>
    <span
      className={`text-[11px] text-center ${
        warnt ? 'text-amber-500 font-semibold' : 'dark:text-zinc-500 text-gray-500'
      }`}
    >
      {label}
    </span>
  </div>
);

// Bei Farben ist der Grund fachlich besonders aufschlussreich.
//
// „Passt nicht zur Marke" heißt: das Verfahren hat richtig gerechnet, der
// Betreiber will nur einen anderen Ton — daraus lernt der Vorschlag nichts.
// „Kontrast reicht trotzdem nicht" heißt dagegen, dass die Rechnung selbst
// danebenlag. Ohne diese Unterscheidung stünden beide als „abgelehnt" da und
// die Quote wäre irreführend.
const KONTRAST_ABLEHNGRUENDE = [
  'Passt nicht zur Marke',
  'Kontrast reicht trotzdem nicht',
  'Falsche Stelle getroffen',
  'Farbe wird woanders gebraucht',
  'Anderer Grund',
] as const;

const KontrastFreigabe: React.FC<{
  siteId: string;
  entscheidungen: KontrastEntscheidung[];
  onGeaendert: () => void;
}> = ({ siteId, entscheidungen, onGeaendert }) => {
  const [laeuft, setLaeuft] = useState<number | null>(null);
  const [fehler, setFehler] = useState<Record<number, string>>({});
  const [eigene, setEigene] = useState<Record<number, string>>({});
  const [offenerEditor, setOffenerEditor] = useState<number | null>(null);
  // Welche Zeile gerade nach einem Ablehnungsgrund fragt
  const [grundFuer, setGrundFuer] = useState<number | null>(null);

  const entscheiden = useCallback(
    async (index: number, approved: boolean, grund?: string) => {
      setLaeuft(index);
      setFehler((f) => ({ ...f, [index]: '' }));
      try {
        await apiClient.post('/api/accessibility/approve-kontrast', {
          site_id: siteId,
          index,
          approved,
          eigene_farbe: approved ? eigene[index] || null : null,
          ablehngrund: approved ? undefined : grund,
        });
        setOffenerEditor(null);
        setGrundFuer(null);
        onGeaendert();
      } catch (e: unknown) {
        const detail = (e as { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail;
        setFehler((f) => ({ ...f, [index]: detail || 'Freigabe fehlgeschlagen.' }));
      } finally {
        setLaeuft(null);
      }
    },
    [siteId, eigene, onGeaendert],
  );

  if (!entscheidungen.length) return null;

  const offen = entscheidungen.filter((e) => e.freigabe === 'pending');
  const stellenOffen = offen.reduce((s, e) => s + (e.stellen || 0), 0);

  return (
    <section>
      <h2 className="flex items-center gap-2 text-sm font-semibold dark:text-zinc-200 text-gray-800 mb-1">
        <Palette className="w-4 h-4 text-amber-400" /> Farben &amp; Kontrast
        <span className="dark:text-zinc-500 text-gray-500 font-normal">
          (WCAG 1.4.3 · {entscheidungen.length} Entscheidung
          {entscheidungen.length === 1 ? '' : 'en'})
        </span>
      </h2>

      {offen.length > 0 && (
        <p className="text-xs dark:text-zinc-400 text-gray-600 mb-3 max-w-3xl">
          <strong>{offen.length} Freigabe{offen.length === 1 ? '' : 'n'} genügen für{' '}
          {stellenOffen} Fundstelle{stellenOffen === 1 ? '' : 'n'}.</strong>{' '}
          Dieselbe Farbkombination kommt auf Ihrer Seite mehrfach vor — Sie
          entscheiden je Farbe, nicht je Fundstelle. Jeder Vorschlag behält
          Farbton und Sättigung und wurde im Browser nachgemessen.
        </p>
      )}

      <div className="space-y-3">
        {entscheidungen.map((e) => {
          const erledigt = e.freigabe !== 'pending';
          return (
            <div
              key={e.index}
              className={`rounded-xl border p-4 ${
                e.freigabe === 'approved'
                  ? 'border-green-500/30 bg-green-500/5'
                  : e.freigabe === 'rejected'
                  ? 'dark:border-zinc-700/50 border-gray-200 opacity-60'
                  : 'dark:border-zinc-700 border-gray-200 dark:bg-zinc-900/40 bg-white'
              }`}
            >
              <div className="flex flex-wrap items-start gap-4">
                <Probe vorn={e.vordergrund} hinten={e.hintergrund}
                       label={`jetzt · ${e.ist_ratio}:1`} />
                {e.loesbar && e.vorschlag && (() => {
                  const farbe = eigene[e.index] || e.vorschlag;
                  const eigen = eigene[e.index] ? ratio(farbe, e.hintergrund) : null;
                  const gezeigt = eigen ?? e.neue_ratio;
                  const reicht = gezeigt !== null && gezeigt >= e.ziel_ratio;
                  return (
                    <>
                      <span className="self-center dark:text-zinc-600 text-gray-600 dark:text-gray-400">→</span>
                      <Probe
                        vorn={farbe}
                        hinten={e.hintergrund}
                        warnt={!reicht}
                        label={gezeigt === null
                          ? 'neu'
                          : reicht
                          ? `neu · ${gezeigt}:1`
                          : `neu · ${gezeigt}:1 — zu wenig`}
                      />
                    </>
                  );
                })()}

                <div className="flex-1 min-w-[12rem] text-xs dark:text-zinc-400 text-gray-600">
                  <div className="font-mono dark:text-zinc-300 text-gray-700">
                    {e.vordergrund}
                    {e.loesbar && e.vorschlag && ` → ${eigene[e.index] || e.vorschlag}`}
                  </div>
                  <div className="mt-1">
                    betrifft <strong>{e.stellen}</strong> Stelle
                    {e.stellen === 1 ? '' : 'n'} · gefordert {e.ziel_ratio}:1
                  </div>
                  {!e.loesbar && (
                    <div className="mt-1.5 flex items-start gap-1.5 text-amber-500">
                      <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 mt-px" />
                      <span>{e.hinweis || 'Mit dieser Vordergrundfarbe nicht erreichbar.'}</span>
                    </div>
                  )}
                  {e.freigabe === 'approved' && (
                    <div className="mt-1.5 text-green-500 flex items-center gap-1">
                      <Check className="w-3.5 h-3.5" /> freigegeben — wird ausgeliefert
                    </div>
                  )}
                  {e.freigabe === 'rejected' && (
                    <div className="mt-1.5 dark:text-zinc-500 text-gray-500">abgelehnt</div>
                  )}
                </div>

                {e.loesbar && erledigt && (
                  <button
                    onClick={() => entscheiden(e.index, e.freigabe !== 'approved')}
                    disabled={laeuft !== null}
                    className="inline-flex items-center gap-1.5 rounded-lg dark:hover:bg-zinc-800 hover:bg-gray-100 dark:text-zinc-400 text-gray-500 px-3 py-2 text-xs disabled:opacity-40"
                  >
                    {laeuft === e.index
                      ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      : <Undo2 className="w-3.5 h-3.5" />}
                    {e.freigabe === 'approved' ? 'Zurückziehen' : 'Doch freigeben'}
                  </button>
                )}

                {e.loesbar && !erledigt && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setOffenerEditor(offenerEditor === e.index ? null : e.index)}
                      className="p-2 rounded-lg dark:hover:bg-zinc-800 hover:bg-gray-100 dark:text-zinc-400 text-gray-500"
                      aria-label="Eigene Farbe wählen"
                      title="Eigene Farbe wählen"
                    >
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => setGrundFuer(e.index)}
                      disabled={laeuft !== null}
                      className="p-2 rounded-lg dark:hover:bg-zinc-800 hover:bg-gray-100 dark:text-zinc-400 text-gray-500 disabled:opacity-40"
                      aria-label="Ablehnen"
                    >
                      <X className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => entscheiden(e.index, true)}
                      disabled={laeuft !== null}
                      className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 hover:bg-green-500 text-white px-3 py-2 text-xs font-semibold disabled:opacity-40"
                    >
                      {laeuft === e.index
                        ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        : <Check className="w-3.5 h-3.5" />}
                      Freigeben
                    </button>
                  </div>
                )}
                {grundFuer === e.index && (
                  <div className="mt-3 pt-3 border-t dark:border-zinc-700/50 border-gray-200">
                    <p className="text-xs dark:text-zinc-400 text-gray-600 mb-2">
                      Woran liegt es? Die Angabe verbessert die nächsten Vorschläge.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {KONTRAST_ABLEHNGRUENDE.map((grund) => (
                        <button
                          key={grund}
                          onClick={() => entscheiden(e.index, false, grund)}
                          disabled={laeuft !== null}
                          className="px-2.5 py-1 text-xs rounded-lg border dark:border-zinc-600 border-gray-300 dark:text-zinc-300 text-gray-700 dark:hover:bg-zinc-700 hover:bg-gray-100 disabled:opacity-40"
                        >
                          {grund}
                        </button>
                      ))}
                      <button
                        onClick={() => setGrundFuer(null)}
                        className="px-2.5 py-1 text-xs dark:text-zinc-500 text-gray-500 dark:hover:text-zinc-300 hover:text-gray-700"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {offenerEditor === e.index && (
                <div className="mt-3 flex flex-wrap items-center gap-2 border-t dark:border-zinc-700/50 border-gray-200 pt-3">
                  <label className="text-xs dark:text-zinc-400 text-gray-600">
                    Eigene Farbe:
                  </label>
                  <input
                    type="color"
                    value={eigene[e.index] || e.vorschlag || '#000000'}
                    onChange={(ev) => setEigene((s) => ({ ...s, [e.index]: ev.target.value }))}
                    className="h-8 w-12 rounded border dark:border-zinc-600 border-gray-300 bg-transparent"
                    aria-label="Farbe wählen"
                  />
                  <input
                    type="text"
                    value={eigene[e.index] || e.vorschlag || ''}
                    onChange={(ev) => setEigene((s) => ({ ...s, [e.index]: ev.target.value }))}
                    className="w-28 rounded-lg border dark:border-zinc-600 border-gray-300 dark:bg-zinc-900/50 bg-white px-2 py-1.5 text-xs font-mono dark:text-zinc-200 text-gray-800"
                    aria-label="Farbwert"
                  />
                  <span className="text-[11px] dark:text-zinc-500 text-gray-500">
                    Wird geprüft — erreicht die Farbe {e.ziel_ratio}:1 nicht, wird
                    sie nicht übernommen.
                  </span>
                </div>
              )}

              {fehler[e.index] && (
                <div className="mt-3 flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2">
                  <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
                  <p className="text-xs dark:text-amber-300 text-amber-700">{fehler[e.index]}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default KontrastFreigabe;
