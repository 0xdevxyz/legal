import type React from 'react';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Erste Schritte | Complyo',
};

/**
 * Erste-Schritte-Uebersicht nach dem Vorbild klassischer Produkt-Doku:
 * nummerierte Schritte in Arbeitsreihenfolge, dazu ein Glossar der Begriffe,
 * die im Dashboard vorausgesetzt werden. Bewusst nuechtern — Anleitungen,
 * keine Marketing-Rhetorik.
 *
 * Die Schrittfolge ist dieselbe wie die Sidebar-Gruppierung
 * (Ueberblick -> Pruefen -> Umsetzen -> Verwalten): wer die Doku liest und
 * dann ins Menue schaut, findet dieselbe Ordnung wieder.
 */

const SCHRITTE: Array<{
  titel: string;
  text: React.ReactNode;
}> = [
  {
    titel: 'Website anlegen und ersten Scan starten',
    text: (
      <>
        Geben Sie im{' '}
        <Link href="/" className="text-teal-500 hover:underline">Dashboard</Link>{' '}
        Ihre Domain ein und starten Sie die Analyse. Geprüft werden die Startseite
        und — je nach Tarif — die rechtlich relevanten Unterseiten (Impressum,
        Datenschutz, AGB, Kontakt, Checkout). Der Scan dauert wenige Minuten und
        kostet nichts.
      </>
    ),
  },
  {
    titel: 'Den Score richtig lesen',
    text: (
      <>
        Der Gesamt-Score ist der Mittelwert aus vier Säulen: DSGVO, Cookies,
        Barrierefreiheit und Rechtstexte. Eine Säule auf 0 bedeutet einen
        Totalausfall (z.&nbsp;B. fehlende Datenschutzerklärung) — nicht viele
        Kleinigkeiten. Jeder Befund nennt Rechtsgrundlage, Empfehlung und, wenn
        mehrere Seiten betroffen sind, alle Fundstellen. Was automatisiert nicht
        prüfbar ist, steht als manuelle Prüfanleitung dabei — wir lassen nichts
        stillschweigend aus.
      </>
    ),
  },
  {
    titel: 'Pflichten-Report ausfüllen',
    text: (
      <>
        Der{' '}
        <Link href="/pflichten-report" className="text-teal-500 hover:underline">Pflichten-Report</Link>{' '}
        (12 Fragen, ~2 Minuten) klärt, welche Regulierungen Ihr Unternehmen
        überhaupt betreffen — vom BFSG bis zum EU AI Act. Er schärft die
        Prüfungen und verhindert Befunde, die auf Sie gar nicht zutreffen.
      </>
    ),
  },
  {
    titel: 'Cookie-Banner einbinden',
    text: (
      <>
        Unter{' '}
        <Link href="/cookie-compliance" className="text-teal-500 hover:underline">Cookies</Link>{' '}
        gestalten Sie das Banner und binden es mit einer Script-Zeile ein — die
        Anleitung je CMS steht in den{' '}
        <Link href="/docs/cms" className="text-teal-500 hover:underline">Integration Guides</Link>.
        Einwilligungen werden protokolliert (Nachweispflicht, DSGVO Art. 7).
        Findet der Scan kein Tracking, sagt Ihnen complyo auch das ehrlich:
        dann brauchen Sie gar kein Banner.
      </>
    ),
  },
  {
    titel: 'Fixes prüfen und freigeben',
    text: (
      <>
        Die KI erzeugt Vorschläge — etwa Alt-Texte für Ihre Bilder — und legt sie
        in die{' '}
        <Link href="/accessibility/worklist" className="text-teal-500 hover:underline">Worklist</Link>.
        Nichts davon wird ohne Ihre Freigabe aktiv. Freigegebene Fixes liefern
        Sie auf drei Wegen aus: sofort über das Widget, als Download-Paket, oder
        als Pull Request direkt in Ihr GitHub-Repository — mechanisch angewendet,
        keine KI schreibt in Ihren Code, und jeder PR lässt sich zurücknehmen.
      </>
    ),
  },
  {
    titel: 'Monitoring einschalten',
    text: (
      <>
        Beobachtete Websites werden täglich auf Änderungen geprüft; ein Vollscan
        läuft nur, wenn sich etwas geändert hat, ein Turnus fällig ist oder sich
        die Rechtslage ändert. Benachrichtigt werden Sie nur, wenn etwas
        schlechter wird — Score-Sturz oder neue kritische Befunde. Die{' '}
        <Link href="/journey" className="text-teal-500 hover:underline">Journey</Link>{' '}
        führt Sie durch die fünf Phasen bis zur laufenden Überwachung.
      </>
    ),
  },
];

const GLOSSAR: Array<{ begriff: string; erklaerung: string }> = [
  {
    begriff: 'Säule',
    erklaerung:
      'Einer der vier Prüfbereiche: DSGVO, Cookies, Barrierefreiheit, Rechtstexte. Jede Säule hat einen eigenen Score von 0 bis 100.',
  },
  {
    begriff: 'Befund',
    erklaerung:
      'Ein konkreter Verstoß oder eine Lücke, mit Schweregrad (kritisch / Warnung / Hinweis), Rechtsgrundlage und Empfehlung. Derselbe Mangel auf mehreren Seiten ist EIN Befund mit mehreren Fundstellen.',
  },
  {
    begriff: 'Fundstelle',
    erklaerung:
      'Die Seite(n) Ihrer Website, auf denen ein Befund auftritt. Beim Mehrseiten-Scan an jedem Befund ausklappbar.',
  },
  {
    begriff: 'Worklist',
    erklaerung:
      'Die Prüfliste für KI-Vorschläge (z. B. Alt-Texte). Erst Ihre Freigabe schaltet einen Vorschlag live — vorher verlässt nichts das System.',
  },
  {
    begriff: 'Fix-Manifest',
    erklaerung:
      'Der Bestand aller freigegebenen Fixes einer Website. Widget, WordPress-Plugin, Download-Paket und Pull Request lesen alle aus derselben Quelle.',
  },
  {
    begriff: 'Deep Scan',
    erklaerung:
      'Die Tiefenprüfung der Cookie-Landschaft: welche Cookies und Tracker laden, bevor eine Einwilligung vorliegt — je Dienst klassifiziert.',
  },
  {
    begriff: 'Manuelle Prüfanleitung',
    erklaerung:
      'Für Kriterien, die keine Maschine prüfen kann (z. B. Tastaturbedienung mit Screenreader), liefert complyo eine Schritt-für-Schritt-Anleitung statt zu schweigen. Automatisierte Prüfungen decken branchenüblich nur 30–40 % der WCAG-Kriterien ab.',
  },
  {
    begriff: 'Expert-Service',
    erklaerung:
      'Wir setzen die Befunde auf Ihrer Website selbst um und dokumentieren das Ergebnis, als Dienstleistung mit Festpreis. Für KMU kann eine BAFA-Förderung in Frage kommen.',
  },
];

export default function ErsteSchrittePage() {
  return (
    <div className="px-4 sm:px-6 py-6">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-12">
          <h1 className="text-4xl font-bold dark:text-white text-gray-900 mb-4">Erste Schritte</h1>
          <p className="dark:text-zinc-400 text-gray-600 text-lg">
            Von der ersten Analyse bis zur laufenden Überwachung, die
            sechs Schritte, in genau der Reihenfolge, in der sie sinnvoll sind.
          </p>
        </div>

        <ol className="space-y-6 mb-16">
          {SCHRITTE.map((s, i) => (
            <li
              key={s.titel}
              className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-2xl p-6 flex gap-4"
            >
              <span
                aria-hidden
                className="flex-shrink-0 w-8 h-8 rounded-full bg-teal-500/15 text-teal-500 font-bold text-sm flex items-center justify-center"
              >
                {i + 1}
              </span>
              <div>
                <h2 className="text-lg font-bold dark:text-white text-gray-900 mb-1.5">{s.titel}</h2>
                <p className="dark:text-zinc-400 text-gray-600 text-sm leading-relaxed">{s.text}</p>
              </div>
            </li>
          ))}
        </ol>

        <section>
          <h2 className="text-2xl font-bold dark:text-white text-gray-900 mb-2">Sprachgebrauch</h2>
          <p className="dark:text-zinc-400 text-gray-600 mb-6 text-sm">
            Begriffe, die im Dashboard vorausgesetzt werden.
          </p>
          <dl className="space-y-4">
            {GLOSSAR.map((g) => (
              <div
                key={g.begriff}
                className="dark:bg-zinc-900 bg-white border dark:border-zinc-800 border-gray-200 rounded-xl p-4"
              >
                <dt className="font-semibold dark:text-white text-gray-900 text-sm">{g.begriff}</dt>
                <dd className="dark:text-zinc-400 text-gray-600 text-sm mt-1 leading-relaxed">{g.erklaerung}</dd>
              </div>
            ))}
          </dl>
        </section>
      </div>
    </div>
  );
}
