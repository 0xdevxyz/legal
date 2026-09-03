'use client';

/**
 * Dauerhafte Orientierung — für JEDEN Besuch, nicht nur den ersten.
 *
 * Der Einführungsassistent lief bisher genau einmal und war danach für immer
 * weg (localStorage-Flag). Damit war der Nutzer, der ein halbes Jahr nicht
 * hereingeschaut hat, weil alles in Ordnung war, beim Wiederkommen genauso
 * orientierungslos wie ein Neuer — nur ohne Hilfe.
 *
 * Dieses Band steht deshalb immer oben und beantwortet immer dieselben drei
 * Fragen, in derselben Reihenfolge:
 *   1. Wo stehe ich?          (Bestand: Seiten, Score, offene Punkte)
 *   2. Was ist passiert?      (Veränderung seit dem letzten Besuch)
 *   3. Was ist als Nächstes?  (genau EIN Schritt, nie eine Auswahl)
 *
 * Der nächste Schritt ergibt sich aus einer festen Rangfolge, damit er
 * berechenbar bleibt: ohne Seite prüfen → veraltetes Ergebnis auffrischen →
 * kritische Punkte beheben → Rechtsänderungen sichten → nichts zu tun.
 */

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Compass, ArrowRight, ChevronDown, ScanLine, AlertTriangle, Scale, CheckCircle2,
} from 'lucide-react';
import { useDashboardStore } from '@/stores/dashboard';
import { useDashboardMetrics } from '@/hooks/useMetrics';
import { apiClient as httpApiClient } from '@/lib/api-client';

const BESUCH_SCHLUESSEL = 'complyo_letzter_besuch';
const ERKLAERUNG_SCHLUESSEL = 'complyo_erklaerung_offen';
const VERALTET_NACH_TAGEN = 30;

type Schritt = {
  titel: string;
  begruendung: string;
  knopf: string;
  icon: React.ComponentType<{ className?: string }>;
  aktion: () => void;
  ton: 'handeln' | 'ruhe';
};

function tageSeit(zeitpunkt?: string | null): number | null {
  if (!zeitpunkt) return null;
  const t = new Date(zeitpunkt).getTime();
  if (Number.isNaN(t)) return null;
  return Math.floor((Date.now() - t) / 86_400_000);
}

function tageText(tage: number): string {
  if (tage <= 0) return 'heute';
  if (tage === 1) return 'gestern';
  if (tage < 31) return `vor ${tage} Tagen`;
  const monate = Math.round(tage / 30);
  return monate === 1 ? 'vor etwa einem Monat' : `vor etwa ${monate} Monaten`;
}

export const Orientierungsband: React.FC = () => {
  const router = useRouter();
  const { currentWebsite, metrics } = useDashboardStore();
  const { metrics: apiMetrics, isLoading } = useDashboardMetrics();

  const [letzterBesuch, setLetzterBesuch] = useState<string | null>(null);
  const [neueUpdates, setNeueUpdates] = useState(0);
  const [erklaerungOffen, setErklaerungOffen] = useState(false);

  // Den vorigen Besuch lesen, BEVOR der aktuelle gestempelt wird — sonst
  // vergleicht man gegen "jetzt" und die Antwort ist immer "nichts Neues".
  useEffect(() => {
    if (typeof localStorage === 'undefined') return;
    setLetzterBesuch(localStorage.getItem(BESUCH_SCHLUESSEL));
    localStorage.setItem(BESUCH_SCHLUESSEL, new Date().toISOString());
    setErklaerungOffen(localStorage.getItem(ERKLAERUNG_SCHLUESSEL) === 'ja');
  }, []);

  useEffect(() => {
    httpApiClient
      .get<{ unread_count: number }>('/api/notifications', { unread_only: true, limit: 1 })
      .then((d) => setNeueUpdates(d?.unread_count ?? 0))
      .catch(() => setNeueUpdates(0));
  }, []);

  const erklaerungUmschalten = () => {
    const neu = !erklaerungOffen;
    setErklaerungOffen(neu);
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem(ERKLAERUNG_SCHLUESSEL, neu ? 'ja' : 'nein');
    }
  };

  const anzahlSeiten = apiMetrics?.websites ?? metrics.websites ?? 0;
  const kritisch = apiMetrics?.criticalIssues ?? metrics.criticalIssues ?? 0;
  const schnitt = apiMetrics?.totalScore ?? metrics.totalScore ?? 0;
  const scanAlter = tageSeit(currentWebsite?.lastScan);
  const besuchAlter = tageSeit(letzterBesuch);

  // ---- Frage 1: Wo stehe ich? ----------------------------------------
  const bestand = anzahlSeiten === 0
    ? 'Noch keine Website geprüft'
    : `${anzahlSeiten} ${anzahlSeiten === 1 ? 'Website' : 'Websites'} · Ø ${schnitt} von 100 · ` +
      `${kritisch} ${kritisch === 1 ? 'kritischer Punkt' : 'kritische Punkte'} offen`;

  // ---- Frage 2: Was ist passiert? ------------------------------------
  const veraenderung: string[] = [];
  if (besuchAlter !== null && besuchAlter >= 1) {
    veraenderung.push(`Ihr letzter Besuch war ${tageText(besuchAlter)}`);
  }
  if (neueUpdates > 0) {
    veraenderung.push(
      `${neueUpdates} ${neueUpdates === 1 ? 'Rechtsänderung' : 'Rechtsänderungen'} ungelesen`,
    );
  }
  if (scanAlter !== null) {
    veraenderung.push(`letzte Prüfung ${tageText(scanAlter)}`);
  }

  // ---- Frage 3: Was ist als Nächstes? --------------------------------
  // Feste Rangfolge — der Nutzer soll nie zwischen Vorschlägen wählen müssen.
  const schritt: Schritt = (() => {
    if (anzahlSeiten === 0) {
      return {
        titel: 'Prüfen Sie Ihre erste Website',
        begruendung: 'Ohne Prüfung gibt es nichts zu zeigen. Der erste Durchlauf dauert rund zwei Minuten.',
        knopf: 'Website eintragen',
        icon: ScanLine,
        ton: 'handeln',
        aktion: () => document.getElementById('website-url-input')?.focus(),
      };
    }
    if (scanAlter !== null && scanAlter > VERALTET_NACH_TAGEN) {
      return {
        titel: `Ihr Ergebnis ist ${tageText(scanAlter)} entstanden`,
        begruendung: 'Websites und Rechtslage ändern sich. Ein frischer Durchlauf sagt Ihnen, ob der Stand noch trägt.',
        knopf: 'Jetzt neu prüfen',
        icon: ScanLine,
        ton: 'handeln',
        aktion: () => window.dispatchEvent(new CustomEvent('complyo:rescan')),
      };
    }
    if (kritisch > 0) {
      return {
        titel: `${kritisch} ${kritisch === 1 ? 'kritischer Punkt wartet' : 'kritische Punkte warten'}`,
        begruendung: 'Kritisch heißt: hier droht konkret ein Bußgeld oder eine Abmahnung. Der Assistent geht sie der Reihe nach mit Ihnen durch.',
        knopf: 'Schritt für Schritt beheben',
        icon: AlertTriangle,
        ton: 'handeln',
        aktion: () => window.dispatchEvent(new CustomEvent('complyo:open-wizard')),
      };
    }
    if (neueUpdates > 0) {
      return {
        titel: `${neueUpdates} ${neueUpdates === 1 ? 'Rechtsänderung' : 'Rechtsänderungen'} seit Ihrem letzten Besuch`,
        begruendung: 'Ihre Seiten sind sauber — aber die Rechtslage hat sich bewegt. Prüfen Sie, ob eine Änderung Sie betrifft.',
        knopf: 'Änderungen ansehen',
        icon: Scale,
        ton: 'handeln',
        aktion: () => document.querySelector('[aria-label="Legal News"]')?.scrollIntoView({ behavior: 'smooth' }),
      };
    }
    return {
      titel: 'Nichts zu tun',
      begruendung: 'Keine kritischen Punkte, keine ungelesenen Rechtsänderungen. Complyo prüft im Hintergrund weiter und meldet sich, wenn sich etwas ändert.',
      knopf: 'Trotzdem neu prüfen',
      icon: CheckCircle2,
      ton: 'ruhe',
      aktion: () => window.dispatchEvent(new CustomEvent('complyo:rescan')),
    };
  })();

  if (isLoading) return null;

  const Symbol = schritt.icon;
  const ruhig = schritt.ton === 'ruhe';

  return (
    <section
      aria-label="Orientierung"
      className="rounded-2xl border bg-white dark:bg-zinc-900/60 border-gray-200 dark:border-zinc-800 overflow-hidden"
    >
      <div className="px-5 py-4">
        {/* Frage 1 + 2: Bestand und Veränderung, bewusst klein und faktisch */}
        <div className="flex items-center gap-2 mb-3 flex-wrap">
          <Compass className="w-4 h-4 shrink-0" style={{ color: 'var(--lime)' }} aria-hidden />
          <span className="text-sm font-semibold text-gray-900 dark:text-white">{bestand}</span>
          {veraenderung.length > 0 && (
            <span className="text-sm text-gray-500 dark:text-zinc-400">
              — {veraenderung.join(' · ')}
            </span>
          )}
        </div>

        {/* Frage 3: genau ein nächster Schritt */}
        <div
          className={`flex items-start gap-4 rounded-xl p-4 border ${
            ruhig
              ? 'bg-emerald-50 dark:bg-emerald-500/5 border-emerald-200 dark:border-emerald-500/25'
              : 'bg-[#25bac8]/5 border-[#25bac8]/30'
          }`}
        >
          <div
            className="p-2.5 rounded-xl shrink-0"
            style={{ background: ruhig ? 'rgba(16,185,129,0.12)' : 'var(--lime-dim)' }}
          >
            <Symbol className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-bold text-gray-900 dark:text-white">{schritt.titel}</p>
            <p className="text-sm text-gray-600 dark:text-zinc-400 mt-0.5 leading-relaxed">
              {schritt.begruendung}
            </p>
          </div>
          <button
            onClick={schritt.aktion}
            className={`shrink-0 flex items-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm transition-all ${
              ruhig
                ? 'border border-gray-300 dark:border-zinc-700 text-gray-700 dark:text-zinc-300 hover:bg-gray-50 dark:hover:bg-zinc-800'
                : 'bg-[#25bac8] text-zinc-950 hover:bg-[#45d6e2]'
            }`}
          >
            {schritt.knopf}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Die Erklärung, was dieses Werkzeug überhaupt tut — dauerhaft
          erreichbar, nicht nur im einmaligen Assistenten. */}
      <button
        onClick={erklaerungUmschalten}
        aria-expanded={erklaerungOffen}
        className="w-full flex items-center justify-between px-5 py-2.5 border-t border-gray-200 dark:border-zinc-800 text-sm text-gray-600 dark:text-zinc-400 hover:bg-gray-50 dark:hover:bg-zinc-800/50 transition-colors"
      >
        <span>Wie complyo arbeitet</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${erklaerungOffen ? 'rotate-180' : ''}`} />
      </button>

      {erklaerungOffen && (
        <div className="px-5 pb-5 pt-1 border-t border-gray-200 dark:border-zinc-800">
          <ol className="space-y-3 text-sm text-gray-600 dark:text-zinc-400">
            {[
              ['Prüfen', 'Wir öffnen Ihre Seite in einem echten Browser und messen nach — auch Unterseiten. Jeder Befund kommt mit Fundstelle und Rechtsgrundlage.'],
              ['Beheben', 'Was sich technisch automatisieren lässt, übernimmt complyo (Alt-Texte, Kontraste, Rechtstexte, Cookie-Banner). Alles andere bekommt eine Anleitung.'],
              ['Nachweisen', 'Nach der Reparatur messen wir erneut und halten fest, was gewirkt hat — und was offen bleibt. Das ist Ihr Nachweis gegenüber Dritten.'],
              ['Überwachen', 'Danach läuft es weiter: neue Rechtslage und Rückschritte auf Ihrer Seite melden sich hier von selbst.'],
            ].map(([titel, text], i) => (
              <li key={titel} className="flex gap-3">
                <span className="shrink-0 w-6 h-6 rounded-full bg-[#25bac8]/15 text-[#1a8a95] dark:text-[#25bac8] flex items-center justify-center text-xs font-bold">
                  {i + 1}
                </span>
                <span>
                  <strong className="text-gray-900 dark:text-white">{titel}.</strong> {text}
                </span>
              </li>
            ))}
          </ol>
          <p className="text-xs text-gray-500 dark:text-zinc-500 mt-4 leading-relaxed">
            Was complyo <strong>nicht</strong> tut: 100 % versprechen. Teile der Barrierefreiheit
            brauchen ein menschliches Urteil — die stehen als „manuell zu prüfen" ausgewiesen da,
            statt still durchzurutschen.
          </p>
        </div>
      )}
    </section>
  );
};

export default Orientierungsband;
