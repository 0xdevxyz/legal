'use client';

/**
 * Barrierefreiheit-Worklist
 * =========================
 * Vereinheitlichte Review-Ansicht über alle Fix-Typen des Fix-Manifests:
 *  - Alt-Texte (WCAG 1.1.1, HITL: Review nötig)
 *  - Link-Zweck (WCAG 2.4.4, HITL: Review nötig)
 *  - Dokumentweite Fixes (lang/skip-link/landmark/css, auto-sicher, read-only)
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
  fix_type: string;
  payload: Record<string, unknown>;
  wcag_criterion?: string;
  confidence: number;
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
  document_fixes: { items: DocItem[]; count: number };
  totals: { needs_review: number; live: number };
  pr_deliverable?: PrDeliverable;
  kontrast?: KontrastBlock;
}

const EMPTY: Worklist = {
  success: true,
  alt_texts: { pending: [], approved: [], approved_count: 0, pending_count: 0 },
  link_fixes: { pending: [], approved: [], approved_count: 0, pending_count: 0 },
  document_fixes: { items: [], count: 0 },
  totals: { needs_review: 0, live: 0 },
  pr_deliverable: { deliverable: 0, manifest_only: 0 },
  kontrast: { entscheidungen: [], offen: 0, freigegeben: 0, stellen_offen: 0 },
};

const DOC_LABEL: Record<string, string> = {
  'html-lang': 'Sprache der Seite (lang)',
  'skip-link': 'Skip-Link „Zum Inhalt springen“',
  'landmark-main': 'Hauptinhalts-Landmark (main)',
  'css-rule': 'Fokus-/Kontrast-CSS',
};

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

      {/* Dokumentweite Fixes (read-only, auto-sicher) */}
      <section>
        <h2 className="flex items-center gap-2 text-sm font-semibold text-zinc-200 mb-3">
          <FileCheck2 className="w-4 h-4 text-green-400" /> Dokumentweite Fixes
          <span className="text-zinc-500 font-normal">(auto-sicher · {data.document_fixes.count} live)</span>
        </h2>
        {data.document_fixes.items.length === 0 ? (
          <p className="text-xs text-zinc-500">Keine dokumentweiten Fixes.</p>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            {data.document_fixes.items.map((d) => (
              <div key={d.fix_type} className="bg-white/60 dark:bg-zinc-900/60 border border-green-500/20 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="text-sm text-zinc-200">{DOC_LABEL[d.fix_type] ?? d.fix_type}</div>
                  {d.wcag_criterion && <div className="text-xs text-zinc-500">WCAG {d.wcag_criterion}</div>}
                </div>
                <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> aktiv</span>
              </div>
            ))}
          </div>
        )}
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
