'use client';

/**
 * Barrierefreiheit-Worklist
 * =========================
 * Vereinheitlichte Review-Ansicht über alle Fix-Typen des Fix-Manifests:
 *  - Alt-Texte (WCAG 1.1.1, HITL: Review nötig)
 *  - Link-Zweck (WCAG 2.4.4, HITL: Review nötig)
 *  - Dokumentweite Fixes (lang/skip-link/landmark/css)
 *
 * Nur freigegebene Fixes werden vom Manifest an die Channels (WP/HTML/SPA) ausgeliefert.
 * Datenquelle: GET /api/accessibility/worklist?site_id=… (ein Call bedient die Seite).
 */

import { useCallback, useEffect, useState } from 'react';
import { CheckCircle, XCircle, Loader2, RefreshCw, ImageIcon, Link2, FileCheck2, Info } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useActiveSite } from '@/contexts/ActiveSiteContext';
import { generateSiteId } from '@/lib/siteIdUtils';
import PullRequestCard from './PullRequestCard';
import KontrastFreigabe, { type KontrastEntscheidung } from './KontrastFreigabe';
import { eingriffeAus, messungAus, alsText } from './dokBeleg';

interface AltItem {
  id: number;
  page_url: string;
  image_src: string;
  image_filename: string;
  suggested_alt: string;
  confidence: number;
  surrounding_text?: string;
  status: string;
}

interface LinkItem {
  id: number;
  page_url: string;
  link_href: string;
  link_text: string;
  suggested_label: string;
  confidence: number;
  surrounding_text?: string;
  status: string;
}

interface DocItem {
  id: number;
  fix_type: string;
  payload: Record<string, unknown>;
  wcag_criterion?: string;
  confidence: number;
  // 'mensch' = jemand hat entschieden. 'automatik' oder leer = läuft live,
  // aber niemand hat es je beurteilt. Genau diese laufen seit Wochen auf
  // Kundenseiten, und genau sie verfälschen jede Annahmequote.
  entscheidung_quelle?: string | null;
  // Kommt vom Backend mit (get_document_fixes_for_site) und ist der einzige
  // Weg, die Reparatur an Ort und Stelle nachzusehen.
  page_url?: string | null;
}

/**
 * Was der PR-Weg von den freigegebenen Fixes wirklich in Code schreiben kann.
 * Kommt vom Backend (fix_patch_builder.zaehle_pr_faehig) — die Regel darf hier
 * nicht nachgebaut werden, sonst verspricht der Knopf irgendwann etwas
 * anderes, als der Patch-Builder liefert.
 */
interface PrDeliverable {
  deliverable: number;
  manifest_only: number;
}

interface KontrastBlock {
  entscheidungen: KontrastEntscheidung[];
  offen: number;
  freigegeben: number;
  stellen_offen: number;
}

interface Worklist {
  success: boolean;
  alt_texts: { pending: AltItem[]; approved: AltItem[]; approved_count: number; pending_count: number };
  link_fixes: { pending: LinkItem[]; approved: LinkItem[]; approved_count: number; pending_count: number };
  document_fixes: { items: DocItem[]; count: number; pending: DocItem[]; pending_count: number };
  totals: { needs_review: number; live: number };
  pr_deliverable?: PrDeliverable;
  kontrast?: KontrastBlock;
}

const EMPTY: Worklist = {
  success: true,
  alt_texts: { pending: [], approved: [], approved_count: 0, pending_count: 0 },
  link_fixes: { pending: [], approved: [], approved_count: 0, pending_count: 0 },
  document_fixes: { items: [], count: 0, pending: [], pending_count: 0 },
  totals: { needs_review: 0, live: 0 },
  pr_deliverable: { deliverable: 0, manifest_only: 0 },
  kontrast: { entscheidungen: [], offen: 0, freigegeben: 0, stellen_offen: 0 },
};

const DOC_LABEL: Record<string, string> = {
  'html-lang': 'Sprache der Seite (lang)',
  'skip-link': 'Skip-Link „Zum Inhalt springen“',
  'landmark-main': 'Hauptinhalts-Landmark (main)',
  'css-rule': 'Fokus-/Kontrast-CSS',
  'struktur': 'Überschriften-Struktur',
  // Stand als roher Schluessel „kontrast-css" auf der Karte.
  'kontrast-css': 'Farben & Kontrast',
};

/**
 * Was eine dokumentweite Reparatur konkret an der Seite tut.
 *
 * Die Karte zeigte bis hierhin „Überschriften-Struktur · WCAG 1.3.1" und zwei
 * Knöpfe, sonst nichts. Wer so gefragt wird, ob eine Reparatur „passt", kann
 * es nicht wissen: der Selektor, der gesetzte Wert, die Begründung und die
 * Messung vorher/nachher stehen im payload, den die Worklist ohnehin
 * mitliefert — das Frontend hat sie verworfen. Eine Freigabe ohne Einsicht
 * ist dieselbe Scheinzustimmung, gegen die diese Karte antritt.
 */
function DokBeleg({ d }: { d: DocItem }) {
  const p = (d.payload ?? {}) as Record<string, unknown>;
  const eingriffe = eingriffeAus(d.fix_type, p);
  const messung = messungAus(p);
  const seite = alsText(d.page_url);

  if (eingriffe.length === 0 && messung.length === 0) {
    return (
      <p className="mt-2 text-xs text-zinc-500">
        Zu dieser Reparatur ist nichts weiter hinterlegt — ohne Beleg lieber ablehnen.
      </p>
    );
  }

  const sichtbar = eingriffe.slice(0, 6);
  const rest = eingriffe.length - sichtbar.length;

  return (
    <div className="mt-2 space-y-1.5">
      {sichtbar.map((e, i) => (
        <div key={i} className="text-xs">
          <code className="text-zinc-300 break-all">{e.was}</code>
          {e.wo && (
            <>
              <span className="text-zinc-600"> an </span>
              <code className="text-zinc-400 break-all">{e.wo}</code>
            </>
          )}
          {e.grund && <div className="text-zinc-500 mt-0.5">{e.grund}</div>}
        </div>
      ))}
      {rest > 0 && (
        <div className="text-xs text-zinc-500">und {rest} weitere Regel{rest === 1 ? '' : 'n'} derselben Art</div>
      )}
      {messung.length > 0 && (
        <div className="text-xs text-zinc-400 pt-1">
          Gemessen:{' '}
          {messung.map((m, i) => (
            <span key={m.regel}>
              {i > 0 && ', '}
              <code className="text-zinc-400">{m.regel}</code> {m.vorher} → {m.nachher}
            </span>
          ))}
        </div>
      )}
      {seite && (
        <a href={seite} target="_blank" rel="noopener noreferrer"
          className="inline-block text-xs text-blue-400 hover:text-blue-300 pt-0.5">
          Seite öffnen und nachsehen ↗
        </a>
      )}
    </div>
  );
}

// Feste Ablehnungsgründe statt Freitext.
//
// Der Generator (ai_alt_text_generator.py) legt dem Modell Ablehnungsgründe
// vor, wenn es den nächsten Vorschlag macht. Freitext allein ließe sich nicht
// zusammenzählen: aus fünfzig verschiedenen Formulierungen für dasselbe
// Problem wird kein Muster. Feste Gründe sind auswertbar, das Zusatzfeld
// fängt den Rest.
//
// Bis 04.09.2026 fragte die Oberfläche gar nicht nach einem Grund. Ergebnis:
// 42 Entscheidungen in der Datenbank, davon 42 Zustimmungen. Aus lauter
// Zustimmung lernt niemand etwas — erst die Ablehnung sagt, wo ein Verfahren
// danebenliegt.
// Eigene Gründe je Befundtyp: ein Linktext scheitert an anderem als ein
// Alt-Text. „Zu allgemein" passt bei beiden, „Bildinhalt falsch beschrieben"
// nur beim einen — eine gemeinsame Liste hätte bei jedem Typ die Hälfte der
// Auswahl unbrauchbar gemacht.
// Struktur- und Skip-Link-Reparaturen greifen ins Seitengerüst ein. Der
// Unterschied zwischen „an der falschen Stelle" und „brauchen wir nicht" ist
// dabei entscheidend: das erste ist ein Fehler des Verfahrens, das zweite eine
// Eigenheit der Website. Ohne die Unterscheidung stünde beides als „abgelehnt"
// da und die Quote wäre irreführend.
const DOK_ABLEHNGRUENDE = [
  'An der falschen Stelle eingefügt',
  'Ist schon vorhanden',
  'Bricht das Layout',
  'Brauchen wir auf dieser Seite nicht',
  'Anderer Grund',
] as const;

const LINK_ABLEHNGRUENDE = [
  'Beschreibt das Ziel falsch',
  'Zu allgemein, sagt nichts aus',
  'Zu lang',
  'Bestehender Text war besser',
  'Anderer Grund',
] as const;

const ABLEHNGRUENDE = [
  'Bildinhalt falsch beschrieben',
  'Zu allgemein, sagt nichts aus',
  'Zu lang',
  'Bild ist reine Dekoration',
  'Firmen- oder Produktname fehlt',
  'Anderer Grund',
] as const;


/**
 * Ein neuer Reparaturvorschlag wartet auf eine Entscheidung.
 *
 * Warum es ihn gibt: Ein freigegebener Fix wird beim naechsten Scan bewusst
 * NICHT ueberschrieben, sonst setzte jeder Wiederholungsscan eine erteilte
 * Freigabe zurueck und die Reparatur verschwaende still von der Website. Der
 * neue Vorschlag wandert stattdessen in den Payload.
 *
 * Bis zum 09.09.2026 endete er dort. Das Feld wurde nirgends gelesen — nicht
 * im Dashboard, nicht im Widget, nicht im Backend. Gemessen lagen fuenf
 * Vorschlaege darin, der aelteste seit vier Wochen. Auf panoart360.de hiess
 * das: die laufende Struktur-Reparatur raeumt 51 Fundstellen auf 16 ab,
 * waehrend im selben Datensatz eine wartete, die auf 4 kommt.
 *
 * Eine Warteschlange ohne Ausgang ist schlimmer als keine: sie sieht von
 * innen aus wie ein erledigter Schritt.
 */
function NeuerVorschlag({ d, busy, onEntscheiden }: {
  d: DocItem;
  busy: boolean;
  onEntscheiden: (uebernehmen: boolean) => void;
}) {
  const p = (d.payload ?? {}) as Record<string, unknown>;
  const vorschlag = p.neuer_vorschlag as Record<string, unknown> | undefined;
  if (!vorschlag) return null;

  // Der Vergleich, auf den es ankommt: beide Zahlen sind im Browser gemessen,
  // vorher und nachher, auf derselben Seite.
  const zahl = (q: Record<string, unknown> | undefined, k: string) =>
    typeof q?.[k] === 'number' ? (q[k] as number) : null;
  const altVor = zahl(p, 'vorher');
  const altNach = zahl(p, 'nachher');
  const neuVor = zahl(vorschlag, 'vorher');
  const neuNach = zahl(vorschlag, 'nachher');
  const messbar = altVor !== null && altNach !== null && neuNach !== null;
  const besser = messbar && (neuNach as number) < (altNach as number);

  return (
    <div className="mt-3 pt-3 border-t border-amber-500/30">
      <div className="text-xs text-amber-300/90 mb-2">
        Ein neuerer Scan schlägt eine andere Fassung vor. Bis Sie entscheiden,
        bleibt die laufende aktiv.
      </div>
      {messbar && (
        <div className="text-xs text-zinc-400 mb-2">
          <div>läuft: {altVor} → {altNach} Fundstellen</div>
          <div className={besser ? 'text-green-400' : undefined}>
            neu: {neuVor ?? altVor} → {neuNach} Fundstellen
            {besser && ` (${(altNach as number) - (neuNach as number)} weniger)`}
          </div>
        </div>
      )}
      <div className="mb-2">
        <DokBeleg d={{ ...d, payload: vorschlag }} />
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onEntscheiden(true)}
          disabled={busy}
          className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg"
        >
          Neue Fassung übernehmen
        </button>
        <button
          onClick={() => onEntscheiden(false)}
          disabled={busy}
          className="px-3 py-1.5 text-xs text-zinc-300 border border-zinc-600 hover:bg-zinc-700 disabled:opacity-40 rounded-lg"
        >
          Laufende behalten
        </button>
      </div>
    </div>
  );
}


export default function AccessibilityWorklist() {
  const { activeSite } = useActiveSite();
  const siteId = activeSite ? generateSiteId(activeSite.url) : '';

  const [data, setData] = useState<Worklist>(EMPTY);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  // Welche Zeile fragt gerade nach einem Ablehnungsgrund
  const [grundFuer, setGrundFuer] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!siteId) return;
    setLoading(true);
    try {
      const res = await apiClient.get<Worklist>('/api/accessibility/worklist', { params: { site_id: siteId } });
      setData(res.data ?? EMPTY);
    } catch {
      setData(EMPTY);
    } finally {
      setLoading(false);
    }
  }, [siteId]);

  useEffect(() => { load(); }, [load]);

  const decideAlt = async (item: AltItem, approved: boolean, grund?: string) => {
    setBusy(`alt-${item.id}`);
    try {
      await apiClient.post('/api/accessibility/approve-alt-text', {
        fix_id: item.id,
        approved,
        custom_alt: edits[`alt-${item.id}`] ?? undefined,
        // Nur bei Ablehnung: der Grund wandert in rejected_reason und von dort
        // in den nächsten Prompt des Generators.
        rejected_reason: approved ? undefined : grund,
      });
      setGrundFuer(null);
      await load();
    } finally {
      setBusy(null);
    }
  };

  const decideLink = async (item: LinkItem, approved: boolean, grund?: string) => {
    setBusy(`link-${item.id}`);
    try {
      await apiClient.post('/api/accessibility/approve-link', {
        fix_id: item.id,
        approved,
        custom_label: edits[`link-${item.id}`] ?? undefined,
        rejected_reason: approved ? undefined : grund,
      });
      setGrundFuer(null);
      await load();
    } finally {
      setBusy(null);
    }
  };

  const decideDok = async (item: DocItem, approved: boolean, grund?: string) => {
    setBusy(`dok-${item.id}`);
    try {
      await apiClient.post('/api/accessibility/approve-dokument', {
        fix_id: item.id,
        approved,
        rejected_reason: approved ? undefined : grund,
      });
      setGrundFuer(null);
      await load();
    } finally {
      setBusy(null);
    }
  };

  // Ein freigegebener Fix wird beim naechsten Scan nicht ueberschrieben — der
  // neue Vorschlag wartet im Payload. Bis zum 09.09.2026 wartete er dort ohne
  // Ausgang: das Feld wurde nirgends gelesen, der aelteste Vorschlag lag vier
  // Wochen. Hier wird die Entscheidung endlich gestellt.
  const entscheideVorschlag = async (item: DocItem, uebernehmen: boolean) => {
    setBusy(`dok-${item.id}`);
    try {
      await apiClient.post('/api/accessibility/vorschlag-entscheiden', {
        fix_id: item.id,
        uebernehmen,
      });
      await load();
    } finally {
      setBusy(null);
    }
  };

  const ziehZurueck = async (art: 'alt' | 'link', item: AltItem | LinkItem) => {
    if (!window.confirm(
      'Diesen Fix zurückziehen? Er verschwindet beim nächsten Abruf des Fix-Manifests von Ihrer Website.'
    )) return;
    setBusy(`${art}-${item.id}`);
    try {
      const endpoint = art === 'alt'
        ? '/api/accessibility/approve-alt-text'
        : '/api/accessibility/approve-link';
      await apiClient.post(endpoint, { fix_id: item.id, approved: false });
      await load();
    } finally {
      setBusy(null);
    }
  };

  // Freigegeben ist nicht gleich beurteilt. Wer hier nicht trennt, zeigt
  // eine Reparatur, die nie jemand gesehen hat, als bestätigt an — und der
  // Lernstand zaehlt sie als Zustimmung.
  const unbestaetigt = data.document_fixes.items.filter(
    (d) => d.entscheidung_quelle !== 'mensch' && d.fix_type !== 'kontrast-css'
  );
  const bestaetigt = data.document_fixes.items.filter(
    (d) => !unbestaetigt.includes(d)
  );

  if (!activeSite) {
    return (
      <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-4 text-sm text-amber-300 flex items-center gap-2">
        <Info className="w-4 h-4" /> Bitte zuerst eine Website auswählen.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Kopf + Zähler */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Barrierefreiheit-Worklist</h1>
          <p className="text-sm text-gray-600 dark:text-zinc-400 mt-1">
            {activeSite.url.replace(/^https?:\/\//, '')} · site-id <code className="text-gray-700 dark:text-zinc-300">{siteId}</code>
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 rounded-lg text-xs bg-amber-500/15 text-amber-300 border border-amber-500/30">
            {data.totals.needs_review} zu prüfen
          </span>
          <span className="px-3 py-1.5 rounded-lg text-xs bg-green-500/15 text-green-300 border border-green-500/30">
            {data.totals.live} live
          </span>
          <button
            onClick={load}
            disabled={loading}
            className="px-3 py-1.5 text-xs text-gray-900 dark:text-white dark:bg-zinc-700 bg-gray-100 hover:bg-zinc-600 disabled:opacity-40 rounded-lg flex items-center gap-1.5"
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            Aktualisieren
          </button>
        </div>
      </div>

      {/* Alt-Texte */}
      <section>
        <h2 className="flex items-center gap-2 text-sm font-semibold text-zinc-200 mb-3">
          <ImageIcon className="w-4 h-4 text-blue-400" /> Alt-Texte
          <span className="text-zinc-500 font-normal">
            ({data.alt_texts.pending_count} offen · {data.alt_texts.approved_count} live)
          </span>
        </h2>
        {data.alt_texts.pending.length === 0 ? (
          <p className="text-xs text-zinc-500">Keine Alt-Texte zur Prüfung.</p>
        ) : (
          <div className="space-y-3">
            {data.alt_texts.pending.map((item) => (
              <div key={item.id} className="bg-white/60 dark:bg-zinc-900/60 border border-amber-500/30 rounded-xl p-4">
                <div className="text-xs text-zinc-500 mb-2 break-all">{item.image_src}</div>
                <input
                  defaultValue={item.suggested_alt}
                  onChange={(e) => setEdits((p) => ({ ...p, [`alt-${item.id}`]: e.target.value }))}
                  className="w-full dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
                />
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-zinc-500">Konfidenz {(item.confidence * 100).toFixed(0)}%</span>
                  <div className="flex gap-2">
                    <button onClick={() => decideAlt(item, true)} disabled={busy === `alt-${item.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Freigeben
                    </button>
                    <button onClick={() => setGrundFuer(`alt-${item.id}`)} disabled={busy === `alt-${item.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-red-600/80 hover:bg-red-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Ablehnen
                    </button>
                  </div>
                </div>
                {grundFuer === `alt-${item.id}` && (
                  <div className="mt-3 pt-3 border-t border-zinc-700/50">
                    <p className="text-xs text-zinc-400 mb-2">
                      Woran liegt es? Die Angabe verbessert die nächsten Vorschläge.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {ABLEHNGRUENDE.map((grund) => (
                        <button
                          key={grund}
                          onClick={() => decideAlt(item, false, grund)}
                          disabled={busy === `alt-${item.id}`}
                          className="px-2.5 py-1 text-xs rounded-lg border border-zinc-600 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                        >
                          {grund}
                        </button>
                      ))}
                      <button
                        onClick={() => setGrundFuer(null)}
                        className="px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-300"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {data.alt_texts.approved.length > 0 && (
          <div className="mt-3 space-y-2">
            {data.alt_texts.approved.map((item) => (
              <div key={item.id} className="bg-white/40 dark:bg-zinc-900/40 border border-green-500/20 rounded-xl px-4 py-2.5 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <span className="text-xs text-green-400 mr-2">live</span>
                  <span className="text-sm text-gray-700 dark:text-zinc-300 break-all">{item.suggested_alt}</span>
                  <div className="text-xs dark:text-zinc-600 text-gray-600 break-all">{item.image_src}</div>
                </div>
                <button onClick={() => ziehZurueck('alt', item)} disabled={busy === `alt-${item.id}`}
                  className="shrink-0 px-3 py-1.5 text-xs text-amber-300 border border-amber-500/30 hover:bg-amber-500/10 disabled:opacity-40 rounded-lg">
                  Zurückziehen
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Link-Zweck */}
      <section>
        <h2 className="flex items-center gap-2 text-sm font-semibold text-zinc-200 mb-3">
          <Link2 className="w-4 h-4 text-purple-400" /> Link-Zweck (WCAG 2.4.4)
          <span className="text-zinc-500 font-normal">
            ({data.link_fixes.pending_count} offen · {data.link_fixes.approved_count} live)
          </span>
        </h2>
        {data.link_fixes.pending.length === 0 ? (
          <p className="text-xs text-zinc-500">Keine Link-Vorschläge zur Prüfung.</p>
        ) : (
          <div className="space-y-3">
            {data.link_fixes.pending.map((item) => (
              <div key={item.id} className="bg-white/60 dark:bg-zinc-900/60 border border-amber-500/30 rounded-xl p-4">
                <div className="text-xs text-zinc-500 mb-2">
                  Linktext <span className="text-gray-700 dark:text-zinc-300">„{item.link_text}“</span>
                  <span className="break-all"> → {item.link_href}</span>
                </div>
                <label className="block text-xs text-zinc-500 mb-1">Vorgeschlagenes aria-label</label>
                <input
                  defaultValue={item.suggested_label}
                  onChange={(e) => setEdits((p) => ({ ...p, [`link-${item.id}`]: e.target.value }))}
                  className="w-full dark:bg-zinc-800 bg-gray-50 border dark:border-zinc-700 border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-white"
                />
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-zinc-500">Konfidenz {(item.confidence * 100).toFixed(0)}%</span>
                  <div className="flex gap-2">
                    <button onClick={() => decideLink(item, true)} disabled={busy === `link-${item.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Freigeben
                    </button>
                    <button onClick={() => setGrundFuer(`link-${item.id}`)} disabled={busy === `link-${item.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-red-600/80 hover:bg-red-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Ablehnen
                    </button>
                  </div>
                </div>
                {grundFuer === `link-${item.id}` && (
                  <div className="mt-3 pt-3 border-t border-zinc-700/50">
                    <p className="text-xs text-zinc-400 mb-2">
                      Woran liegt es? Die Angabe verbessert die nächsten Vorschläge.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {LINK_ABLEHNGRUENDE.map((grund) => (
                        <button
                          key={grund}
                          onClick={() => decideLink(item, false, grund)}
                          disabled={busy === `link-${item.id}`}
                          className="px-2.5 py-1 text-xs rounded-lg border border-zinc-600 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                        >
                          {grund}
                        </button>
                      ))}
                      <button
                        onClick={() => setGrundFuer(null)}
                        className="px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-300"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {data.link_fixes.approved.length > 0 && (
          <div className="mt-3 space-y-2">
            {data.link_fixes.approved.map((item) => (
              <div key={item.id} className="bg-white/40 dark:bg-zinc-900/40 border border-green-500/20 rounded-xl px-4 py-2.5 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <span className="text-xs text-green-400 mr-2">live</span>
                  <span className="text-sm text-gray-700 dark:text-zinc-300">„{item.suggested_label}“</span>
                  <div className="text-xs dark:text-zinc-600 text-gray-600 break-all">{item.link_href}</div>
                </div>
                <button onClick={() => ziehZurueck('link', item)} disabled={busy === `link-${item.id}`}
                  className="shrink-0 px-3 py-1.5 text-xs text-amber-300 border border-amber-500/30 hover:bg-amber-500/10 disabled:opacity-40 rounded-lg">
                  Zurückziehen
                </button>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Farben & Kontrast — die einzigen Fixes, die das Aussehen aendern,
          deshalb je Entscheidung freizugeben statt automatisch live. */}
      {data.kontrast && data.kontrast.entscheidungen.length > 0 && (
        <KontrastFreigabe
          siteId={siteId}
          entscheidungen={data.kontrast.entscheidungen}
          onGeaendert={load}
        />
      )}

      {/* Dokumentweite Fixes.
          Bis 04.09.2026 gingen sie ohne Rückfrage live und standen hier nur
          als „auto-sicher" da. Damit erfuhr complyo nie, dass eine
          Strukturreparatur danebenlag — im Lernstand erschienen sie mit
          100 % Zustimmung, weil niemand gefragt wurde. */}
      <section>
        <h2 className="flex items-center gap-2 text-sm font-semibold text-zinc-200 mb-3">
          <FileCheck2 className="w-4 h-4 text-green-400" /> Dokumentweite Fixes
          <span className="text-zinc-500 font-normal">
            ({data.document_fixes.pending_count} offen · {data.document_fixes.count} live
            {unbestaetigt.length > 0 && `, davon ${unbestaetigt.length} unbestätigt`})
          </span>
        </h2>
        {data.document_fixes.pending.length > 0 && (
          <div className="space-y-3 mb-3">
            {data.document_fixes.pending.map((d) => (
              <div key={`dok-${d.id}`} className="bg-white/60 dark:bg-zinc-900/60 border border-amber-500/30 rounded-xl p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm text-zinc-200">{DOC_LABEL[d.fix_type] ?? d.fix_type}</div>
                    {d.wcag_criterion && <div className="text-xs text-zinc-500">WCAG {d.wcag_criterion}</div>}
                    <DokBeleg d={d} />
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button onClick={() => decideDok(d, true)} disabled={busy === `dok-${d.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Freigeben
                    </button>
                    <button onClick={() => setGrundFuer(`dok-${d.id}`)} disabled={busy === `dok-${d.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-red-600/80 hover:bg-red-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> Ablehnen
                    </button>
                  </div>
                </div>
                {grundFuer === `dok-${d.id}` && (
                  <div className="mt-3 pt-3 border-t border-zinc-700/50">
                    <p className="text-xs text-zinc-400 mb-2">
                      Woran liegt es? Die Angabe verbessert die nächsten Vorschläge.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {DOK_ABLEHNGRUENDE.map((grund) => (
                        <button
                          key={grund}
                          onClick={() => decideDok(d, false, grund)}
                          disabled={busy === `dok-${d.id}`}
                          className="px-2.5 py-1 text-xs rounded-lg border border-zinc-600 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                        >
                          {grund}
                        </button>
                      ))}
                      <button
                        onClick={() => setGrundFuer(null)}
                        className="px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-300"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {/* Läuft live, hat aber nie jemand beurteilt.

            Bis zum 05.09.2026 gingen diese Reparaturen beim Anlegen direkt
            auf 'approved'. Sie stehen seither auf echten Kundenseiten, und in
            der Auswertung sahen sie aus wie einstimmige Zustimmung — dabei
            wurde nie gefragt. Deshalb werden sie hier nicht stillschweigend
            zu den bestätigten gelegt, sondern einmal vorgelegt. */}
        {unbestaetigt.length > 0 && (
          <div className="space-y-3 mb-3">
            <p className="text-xs text-amber-300/90">
              Diese {unbestaetigt.length} Reparatur{unbestaetigt.length === 1 ? '' : 'en'} laufen
              bereits auf Ihrer Website, wurden aber nie bestätigt. Eine kurze Durchsicht
              genügt: „Passt so" ändert nichts, „War falsch" nimmt die Reparatur beim
              nächsten Abruf von der Seite.
            </p>
            {unbestaetigt.map((d) => (
              <div key={`dok-alt-${d.id}`} className="bg-white/60 dark:bg-zinc-900/60 border border-amber-500/30 rounded-xl p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm text-zinc-200">{DOC_LABEL[d.fix_type] ?? d.fix_type}</div>
                    <div className="text-xs text-amber-400/80">läuft live, nie bestätigt</div>
                    {d.wcag_criterion && <div className="text-xs text-zinc-500">WCAG {d.wcag_criterion}</div>}
                    <DokBeleg d={d} />
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <button onClick={() => decideDok(d, true)} disabled={busy === `dok-${d.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-green-600 hover:bg-green-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5" /> Passt so
                    </button>
                    <button onClick={() => setGrundFuer(`dok-${d.id}`)} disabled={busy === `dok-${d.id}`}
                      className="px-3 py-1.5 text-xs text-white bg-red-600/80 hover:bg-red-500 disabled:opacity-40 rounded-lg flex items-center gap-1">
                      <XCircle className="w-3.5 h-3.5" /> War falsch
                    </button>
                  </div>
                </div>
                {grundFuer === `dok-${d.id}` && (
                  <div className="mt-3 pt-3 border-t border-zinc-700/50">
                    <p className="text-xs text-zinc-400 mb-2">
                      Woran liegt es? Die Reparatur verschwindet beim nächsten Abruf von
                      Ihrer Website.
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {DOK_ABLEHNGRUENDE.map((grund) => (
                        <button
                          key={grund}
                          onClick={() => decideDok(d, false, grund)}
                          disabled={busy === `dok-${d.id}`}
                          className="px-2.5 py-1 text-xs rounded-lg border border-zinc-600 text-zinc-300 hover:bg-zinc-700 disabled:opacity-40"
                        >
                          {grund}
                        </button>
                      ))}
                      <button
                        onClick={() => setGrundFuer(null)}
                        className="px-2.5 py-1 text-xs text-zinc-500 hover:text-zinc-300"
                      >
                        Abbrechen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {data.document_fixes.items.length === 0 ? (
          <p className="text-xs text-zinc-500">Keine dokumentweiten Fixes.</p>
        ) : bestaetigt.length > 0 ? (
          <div className="grid sm:grid-cols-2 gap-3">
            {bestaetigt.map((d) => (
              <div key={d.id} className="bg-white/60 dark:bg-zinc-900/60 border border-green-500/20 rounded-xl p-3">
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0">
                    <div className="text-sm text-zinc-200">{DOC_LABEL[d.fix_type] ?? d.fix_type}</div>
                    {d.wcag_criterion && <div className="text-xs text-zinc-500">WCAG {d.wcag_criterion}</div>}
                  </div>
                  <span className="text-xs text-green-400 shrink-0 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> aktiv</span>
                </div>
                {/* Auch das Bestaetigte muss nachlesbar bleiben: nach der
                    Freigabe stand hier nur noch „aktiv", und was da auf der
                    Seite laeuft, war wieder unsichtbar. Zugeklappt, weil diese
                    Karten im Raster stehen und die Frage hier „was laeuft da?"
                    ist, nicht „stimmt das?". */}
                <details className="mt-2">
                  <summary className="text-xs text-zinc-500 hover:text-zinc-300 cursor-pointer">
                    Was diese Reparatur tut
                  </summary>
                  <DokBeleg d={d} />
                </details>
                <NeuerVorschlag
                  d={d}
                  busy={busy === `dok-${d.id}`}
                  onEntscheiden={(uebernehmen) => entscheideVorschlag(d, uebernehmen)}
                />
              </div>
            ))}
          </div>
        ) : null}
      </section>

      {/* Ein-Klick-Auslieferung: freigegebene Fixes als PR ins Kundenrepo.
          Lebt bewusst hier — Freigeben und Ausliefern sind ein Arbeitsgang. */}
      <PullRequestCard
        siteId={siteId}
        approvedCount={data.pr_deliverable?.deliverable ?? 0}
        manifestOnlyCount={data.pr_deliverable?.manifest_only ?? 0}
      />
    </div>
  );
}
