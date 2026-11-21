'use client';

import React from 'react';
import { ArrowLeftRight, Check, Minus, X } from 'lucide-react';
import { PREIS_REGULAER } from '@/components/kampagne/angebot';

/**
 * Vier Wege, die Befunde loszuwerden. Als Kategorien, nicht als Namen.
 *
 * Die Tabelle nennt bewusst keine Wettbewerber. Vergleichende Werbung ist
 * nach § 6 UWG erlaubt, aber nur mit nachprüfbaren Eigenschaften, und für
 * ein einzelnes Produkt müssten wir jede Zelle belegen können. Für Kategorien
 * reicht, was strukturell gilt: Ein Anwalt ändert keinen Quellcode, ein
 * Overlay ändert ihn auch nicht, und wer es selbst macht, zahlt mit Zeit.
 *
 * Die letzte Zeile sagt, wann der andere Weg gewinnt. Sie ist kein
 * Zugeständnis, sondern der Grund, warum der Rest der Tabelle geglaubt wird.
 */
type Zelle = { wert: 'ja' | 'nein' | 'teils'; text: string };

interface Zeile {
  merkmal: string;
  selbst: Zelle;
  anwaltAgentur: Zelle;
  overlay: Zelle;
  complyo: Zelle;
}

const ZEILEN: Zeile[] = [
  {
    merkmal: 'Findet die Befunde in allen vier Bereichen',
    selbst: { wert: 'teils', text: 'Wenn Sie wissen, wonach Sie suchen.' },
    anwaltAgentur: { wert: 'ja', text: 'Nach Aufwand, zum Stichtag des Gutachtens.' },
    overlay: { wert: 'nein', text: 'Nur Barrierefreiheit, und nur an der Oberfläche.' },
    complyo: { wert: 'ja', text: 'Automatisiert, bei jedem Scan.' },
  },
  {
    merkmal: 'Behebt sie im Quellcode',
    selbst: { wert: 'teils', text: 'Sie oder Ihr Entwickler.' },
    anwaltAgentur: { wert: 'teils', text: 'Agentur ja, Anwalt nein.' },
    overlay: { wert: 'nein', text: 'Ein Skript legt sich über die Seite. Das HTML bleibt, wie es ist, und genau das wird geprüft.' },
    complyo: { wert: 'ja', text: 'Im Werkzeug, danach im Browser nachgemessen.' },
  },
  {
    merkmal: 'Nachweis, was wann geprüft und geändert wurde',
    selbst: { wert: 'teils', text: 'Wenn Sie es dokumentieren.' },
    anwaltAgentur: { wert: 'teils', text: 'Das Gutachten, für den Tag, an dem es geschrieben wurde.' },
    overlay: { wert: 'nein', text: 'Kein Protokoll über den Code.' },
    complyo: { wert: 'ja', text: 'Prüfprotokoll je Änderung.' },
  },
  {
    merkmal: 'Bei neuem Urteil oder Gesetz',
    selbst: { wert: 'teils', text: 'Sie müssen es mitbekommen.' },
    anwaltAgentur: { wert: 'teils', text: 'Neuer Auftrag, neue Rechnung.' },
    overlay: { wert: 'nein', text: 'Nichts passiert.' },
    complyo: { wert: 'ja', text: 'Neu-Check, sobald sich die Rechtslage ändert.' },
  },
  {
    merkmal: 'Klärt, ob eine Pflicht für Sie überhaupt gilt',
    selbst: { wert: 'nein', text: 'Rechtsfrage.' },
    anwaltAgentur: { wert: 'ja', text: 'Dafür ist der Anwalt da.' },
    overlay: { wert: 'nein', text: 'Rechtsfrage.' },
    complyo: { wert: 'nein', text: 'Bleibt beim Anwalt. Wir sagen das offen.' },
  },
  {
    merkmal: 'Kosten',
    selbst: { wert: 'teils', text: 'Ihre Zeit, siehe Rechner oben.' },
    anwaltAgentur: { wert: 'teils', text: 'Nach Stundensatz, je Durchgang.' },
    overlay: { wert: 'teils', text: 'Lizenz im Monat, Befund bleibt.' },
    complyo: { wert: 'ja', text: `Scan kostenlos. Beheben ab ${PREIS_REGULAER} im Monat, monatlich kündbar.` },
  },
];

const GEWINNT_WENN = {
  selbst: 'Sie selbst entwickeln, Zeit haben und den Nachweis für sich führen.',
  anwaltAgentur: 'Eine Rechtsfrage offen ist, oder ohnehin ein Relaunch ansteht.',
  overlay: 'Sie den Code nicht anfassen dürfen und nur ein Hilfsmenü für Besucher wollen.',
  complyo: 'Sie die Befunde messbar beheben und belegen wollen, ohne jeden Monat selbst nachzusehen.',
};

const SPALTEN: { key: keyof typeof GEWINNT_WENN; titel: string }[] = [
  { key: 'selbst', titel: 'Selbst machen' },
  { key: 'anwaltAgentur', titel: 'Anwalt oder Agentur' },
  { key: 'overlay', titel: 'Overlay-Widget' },
  { key: 'complyo', titel: 'Complyo' },
];

function Symbol({ wert }: { wert: Zelle['wert'] }) {
  if (wert === 'ja') return <Check className="w-4 h-4 text-green-700 flex-shrink-0 mt-0.5" aria-label="ja" />;
  if (wert === 'nein') return <X className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" aria-label="nein" />;
  return <Minus className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" aria-label="teilweise" />;
}

export default function WegeVergleich() {
  return (
    <section aria-labelledby="wege-titel" className="bg-white rounded-2xl border-2 border-gray-200 p-6 sm:p-8">
      <div className="inline-flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1 mb-4">
        <ArrowLeftRight className="w-4 h-4 text-gray-700" aria-hidden="true" />
        <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Vier Wege
        </span>
      </div>
      <h3 id="wege-titel" className="font-heading text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3">
        Sie haben die Wahl. Das sind die Unterschiede.
      </h3>
      <p className="text-gray-600 leading-relaxed mb-8 max-w-3xl">
        Es gibt mehr als einen Weg, die Befunde oben loszuwerden. Wir nennen alle vier, auch
        die, bei denen wir nicht vorkommen, und sagen zu jedem, wann er der bessere ist.
      </p>

      {/* Ab lg eine Tabelle; darunter je Weg eine Karte. Eine Tabelle mit
          fünf Spalten auf dem Handy liest niemand. */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-0">
          <thead>
            <tr>
              <th scope="col" className="text-left align-bottom pb-3 pr-4 font-semibold text-gray-500 w-[22%]">Merkmal</th>
              {SPALTEN.map((s) => (
                <th
                  key={s.key}
                  scope="col"
                  className={`text-left align-bottom pb-3 px-3 font-bold ${s.key === 'complyo' ? 'text-gray-900 border-t-4 border-akzent-400 pt-3 rounded-t-lg' : 'text-gray-900'}`}
                >
                  {s.titel}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ZEILEN.map((z) => (
              <tr key={z.merkmal} className="border-t border-gray-200">
                <th scope="row" className="text-left align-top py-4 pr-4 font-semibold text-gray-900 border-t border-gray-200">{z.merkmal}</th>
                {SPALTEN.map((s) => {
                  const zelle = z[s.key];
                  return (
                    <td key={s.key} className={`align-top py-4 px-3 border-t border-gray-200 ${s.key === 'complyo' ? 'bg-gray-50' : ''}`}>
                      <div className="flex items-start gap-2">
                        <Symbol wert={zelle.wert} />
                        <span className="text-gray-700 leading-relaxed">{zelle.text}</span>
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
            <tr>
              <th scope="row" className="text-left align-top py-4 pr-4 font-semibold text-gray-900 border-t-2 border-gray-300">Gewinnt, wenn</th>
              {SPALTEN.map((s) => (
                <td key={s.key} className={`align-top py-4 px-3 border-t-2 border-gray-300 text-gray-700 leading-relaxed ${s.key === 'complyo' ? 'bg-gray-50 rounded-b-lg' : ''}`}>
                  {GEWINNT_WENN[s.key]}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="lg:hidden grid grid-cols-1 sm:grid-cols-2 gap-4">
        {SPALTEN.map((s) => (
          <div key={s.key} className={`rounded-xl border-2 p-5 ${s.key === 'complyo' ? 'border-akzent-400 bg-gray-50' : 'border-gray-200 bg-white'}`}>
            <h4 className="font-bold text-gray-900 mb-3">{s.titel}</h4>
            <dl className="space-y-3 text-sm">
              {ZEILEN.map((z) => (
                <div key={z.merkmal}>
                  <dt className="font-semibold text-gray-900">{z.merkmal}</dt>
                  <dd className="flex items-start gap-2 text-gray-700 leading-relaxed">
                    <Symbol wert={z[s.key].wert} />
                    <span>{z[s.key].text}</span>
                  </dd>
                </div>
              ))}
              <div className="pt-3 border-t border-gray-200">
                <dt className="font-semibold text-gray-900">Gewinnt, wenn</dt>
                <dd className="text-gray-700 leading-relaxed">{GEWINNT_WENN[s.key]}</dd>
              </div>
            </dl>
          </div>
        ))}
      </div>
    </section>
  );
}
