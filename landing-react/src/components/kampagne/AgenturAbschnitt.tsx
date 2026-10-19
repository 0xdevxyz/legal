'use client';
import React from 'react';
import { ArrowRight, Check, Building2 } from 'lucide-react';
import { useHerkunft, mitHerkunft } from '@/lib/herkunft';
import { AGENTUR_PREIS_MONAT, AGENTUR_PREIS_JAHR, AGENTUR_PROJEKTE } from './angebot';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.complyo.de';

/**
 * Der Agentur-Tarif als Kaufweg auf der Early-Access-Seite.
 *
 * Seit dem 19.10.2026 steht auf "/" wieder die Warteliste. Inhaber einzelner
 * Websites sichern sich dort den Early-Access-Preis fuer Pro; der Nachlass
 * haengt an einem bestaetigten Platz, nicht an der Registrierung. Agenturen
 * betreuen fremde Websites und brauchen den Platz nicht: ihr Tarif ist
 * regulaer buchbar, ohne Warteliste. Dieser Abschnitt ist der einzige
 * Kaufweg auf der Seite, deshalb stehen die Pflichtangaben vor
 * Vertragsschluss (Netto-Preis, Kuendbarkeit, Unternehmer nach § 14 BGB) hier
 * und nicht nur in den AGB.
 *
 * Die Herkunft (utm) reist mit in die Registrierung, wie beim Knopf in der
 * Preistabelle. Siehe lib/herkunft.ts.
 */
const LEISTUNGEN = [
  `${AGENTUR_PROJEKTE} Projekte inklusive`,
  'Voller Pro-Funktionsumfang je Projekt',
  `Erweiterbar um weitere ${AGENTUR_PROJEKTE} Projekte`,
  'Zentrale Übersicht über alle Domains',
];

export default function AgenturAbschnitt() {
  const herkunft = useHerkunft();
  const buchen = mitHerkunft(APP_URL + '/register?plan=agency', herkunft);

  return (
    <section
      id="agentur"
      aria-labelledby="agentur-titel"
      className="py-16 bg-nacht-900 scroll-mt-16"
    >
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl bg-nacht-800 border border-nacht-700 text-white p-8 sm:p-10 grid grid-cols-1 lg:grid-cols-5 gap-8 lg:gap-12 items-center">
          <div className="lg:col-span-3">
            <div className="inline-flex items-center gap-2 bg-nacht-950/10 rounded-full px-3 py-1 mb-4">
              <Building2 className="w-3.5 h-3.5 text-akzent-400" aria-hidden="true" />
              <span className="text-xs font-semibold uppercase tracking-wide">Für Agenturen</span>
            </div>
            <h2 id="agentur-titel" className="font-heading text-2xl sm:text-3xl font-extrabold mb-3">
              Du betreust fremde Websites? Dann brauchst du keinen Platz auf der Liste.
            </h2>
            <p className="text-gray-300 leading-relaxed mb-6">
              Der Agentur-Tarif ist sofort buchbar: {AGENTUR_PROJEKTE} Projekte mit dem vollen
              Pro-Funktionsumfang, eine Übersicht über alle Domains, Prüfnachweis je Kunde.
              Der Early-Access-Nachlass gilt für Pro im Monatsabo, nicht für den Agentur-Tarif.
            </p>
            <ul className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-2.5">
              {LEISTUNGEN.map((l) => (
                <li key={l} className="flex items-start gap-2.5 text-sm text-gray-200">
                  <Check className="w-4 h-4 text-akzent-400 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <span>{l}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="lg:col-span-2 bg-nacht-900 text-gray-50 rounded-2xl border border-akzent-400/50 p-6">
            <p className="text-sm text-gray-400 mb-1">Agentur</p>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-extrabold">{AGENTUR_PREIS_MONAT}</span>
              <span className="text-sm text-gray-400">/Monat</span>
            </div>
            <p className="text-xs text-gray-400 mt-1 mb-6">oder {AGENTUR_PREIS_JAHR} im Jahr</p>
            <a
              href={buchen}
              className="inline-flex items-center justify-center gap-2 w-full bg-akzent-400 hover:bg-akzent-500 text-gray-900 font-semibold px-5 py-3 rounded-xl transition-colors shadow-md shadow-akzent-900/50"
            >
              Agentur buchen
              <ArrowRight className="w-4 h-4" aria-hidden="true" />
            </a>
            <p className="text-xs text-gray-400 mt-4 leading-relaxed">
              Preis zzgl. MwSt., monatlich kündbar, Zahlung per Karte und den im Checkout
              angezeigten Bezahlarten. Das Angebot richtet sich ausschließlich an Unternehmer
              im Sinne des § 14 BGB; ein Verkauf an Verbraucher findet nicht statt.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
