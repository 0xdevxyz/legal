'use client';

import React from 'react';
import { ShieldCheck, ArrowRight, Check } from 'lucide-react';
import { useHerkunft, mitHerkunft } from '@/lib/herkunft';
import { PLAETZE, PREIS_EARLY, PREIS_REGULAER, AGENTUR_PREIS_MONAT, AGENTUR_PROJEKTE } from '@/components/kampagne/angebot';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.complyo.de';

/**
 * Preis und Risikoumkehr am Ende der Ergebnisseite.
 *
 * Reihenfolge mit Absicht: erst, was wir tragen (Scan kostenlos, ein Fix
 * kostenlos, monatlich kündbar), dann der Preis, dann, was wir NICHT
 * versprechen. Der letzte Block steht hier, weil § 3 Abs. 3 der AGB keine
 * Abmahnsicherheit und keine Bußgeldfreiheit zusichert. Eine Landing, die das
 * Gegenteil andeutet, widerspräche den eigenen AGB und würde im Streit gegen
 * uns ausgelegt. Also steht es offen da. Bei Kunden, die gerade eine Seite
 * voller Befunde gesehen haben, ist das auch das glaubwürdigere Angebot.
 *
 * Die Herkunft (utm) reist mit in die Registrierung, wie bei jedem Kaufweg
 * der Landing. Siehe lib/herkunft.ts.
 */
export default function PreisUndRisikoumkehr({ befunde }: { befunde: number }) {
  const herkunft = useHerkunft();
  const freiStarten = mitHerkunft(`${APP_URL}/register?plan=free`, herkunft);
  const proBuchen = mitHerkunft(`${APP_URL}/register?plan=pro`, herkunft);
  const agenturBuchen = mitHerkunft(`${APP_URL}/register?plan=agency`, herkunft);

  const WIR_TRAGEN = [
    'Der vollständige Scan kostet nichts, auch ohne Registrierung.',
    'Der erste Fix ist im Free-Tarif enthalten. Sie sehen, wie die Reparatur arbeitet, bevor Sie zahlen.',
    'Keine Zahlungsdaten für den Start, keine Mindestlaufzeit, monatlich kündbar.',
    'Jede Änderung wird im Browser nachgemessen und protokolliert. Das Protokoll gehört Ihnen.',
  ];

  return (
    <section aria-labelledby="preis-titel" className="bg-gray-900 rounded-2xl p-6 sm:p-10 text-white">
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 lg:gap-12">
        <div className="lg:col-span-3">
          <div className="inline-flex items-center gap-2 bg-white/10 rounded-full px-3 py-1 mb-4">
            <ShieldCheck className="w-4 h-4 text-akzent-400" aria-hidden="true" />
            <span className="text-xs font-semibold uppercase tracking-wide text-gray-200">
              Das Risiko liegt bei uns
            </span>
          </div>
          <h3 id="preis-titel" className="font-heading text-2xl sm:text-3xl font-extrabold mb-4">
            {befunde === 0
              ? 'Heute sauber. Complyo hält es so und belegt es.'
              : `${befunde} ${befunde === 1 ? 'Befund' : 'Befunde'}. Der erste Fix kostet Sie nichts.`}
          </h3>
          <ul className="space-y-2.5 mb-6">
            {WIR_TRAGEN.map((t) => (
              <li key={t} className="flex items-start gap-2.5 text-sm text-gray-200 leading-relaxed">
                <Check className="w-4 h-4 text-akzent-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                <span>{t}</span>
              </li>
            ))}
          </ul>

          <div className="rounded-xl border border-white/15 bg-white/5 p-4 sm:p-5">
            <p className="text-sm font-semibold text-white mb-1.5">Was wir nicht versprechen</p>
            <p className="text-sm text-gray-300 leading-relaxed">
              Dass Sie niemand abmahnt, und dass keine Behörde je ein Bußgeld verhängt. Das kann
              kein Werkzeug und kein Anwalt zusichern, und wer es tut, verkauft Ihnen etwas anderes
              als Compliance. Wir versprechen, dass Sie belegen können, was Sie geprüft und
              behoben haben, mit Datum und Messung.
            </p>
          </div>
        </div>

        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="bg-white text-gray-900 rounded-2xl p-6 border-2 border-akzent-400">
            <p className="text-sm text-gray-500 mb-1">Pro, eine Domain</p>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-extrabold">{PREIS_REGULAER}</span>
              <span className="text-sm text-gray-500">/Monat</span>
            </div>
            <p className="text-xs text-gray-500 mt-1 mb-5">
              Die ersten {PLAETZE} mit bestätigtem Early-Access-Platz zahlen {PREIS_EARLY} im ersten Jahr.
            </p>
            <a
              href={freiStarten}
              className="inline-flex items-center justify-center gap-2 w-full bg-gray-900 hover:bg-gray-800 text-white font-semibold px-5 py-3 rounded-xl transition-colors"
            >
              {befunde === 0 ? 'Kostenlos registrieren und Befund festhalten' : 'Kostenlos starten, ersten Fix ansehen'}
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </a>
            <a
              href={proBuchen}
              className="inline-flex items-center justify-center gap-2 w-full mt-2 bg-white hover:bg-gray-50 text-gray-900 font-semibold px-5 py-3 rounded-xl border-2 border-gray-200 transition-colors"
            >
              Direkt Pro buchen
            </a>
            <p className="text-xs text-gray-500 mt-4 leading-relaxed">
              Preise netto zzgl. Umsatzsteuer, monatlich kündbar. Das Angebot richtet sich an
              Unternehmer im Sinne des § 14 BGB.
            </p>
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">
            Sie betreuen fremde Websites?{' '}
            <a href={agenturBuchen} className="font-semibold text-white underline underline-offset-2 hover:text-akzent-300">
              Agentur-Tarif
            </a>
            : {AGENTUR_PROJEKTE} Projekte für {AGENTUR_PREIS_MONAT} im Monat.
          </p>
        </div>
      </div>
    </section>
  );
}
