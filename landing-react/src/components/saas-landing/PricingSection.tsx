'use client';
import React from 'react';
import { Check, ArrowRight, Sparkles } from 'lucide-react';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.complyo.de';

type Plan = {
  id: string;
  name: string;
  price: string;
  period: string;
  note?: string;
  description: string;
  features: string[];
  cta: string;
  href: string;
  highlighted?: boolean;
};

const PLANS: Plan[] = [
  {
    id: 'free',
    name: 'Free',
    price: '0 €',
    period: '',
    description: 'Der volle Befund, ohne Kreditkarte.',
    features: [
      'Vollständiger Scan aller vier Säulen',
      'Ein Fix inklusive',
      'Cookie-Banner konfigurierbar – ohne Einbettungscode',
      'Rechtstexte und Barrierefreiheit als Scan und Vorschau',
    ],
    cta: 'Kostenlos starten',
    href: APP_URL + '/register?plan=free',
  },
  {
    id: 'single',
    name: 'Einzelsäule',
    price: '19 €',
    period: '/Monat je Säule',
    description: 'Nur das Thema, das gerade drückt.',
    features: [
      'Eine Säule vollständig freigeschaltet',
      'Wahlweise Cookie und DSGVO, Barrierefreiheit, Rechtstexte oder Monitoring',
      'Jederzeit weitere Säulen dazubuchen',
      'Monatlich kündbar',
    ],
    cta: 'Säule wählen',
    href: APP_URL + '/register?plan=single',
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '49 €',
    period: '/Monat',
    note: 'oder 490 € im Jahr',
    description: 'Alles frei für eine Domain.',
    features: [
      'Alle vier Säulen ohne Limit',
      'Einbettungscode für Cookie-Banner und Widget',
      'Unbegrenzte Fixes und laufendes Monitoring',
      'Domainwechsel über den Support',
    ],
    cta: 'Pro buchen',
    href: APP_URL + '/register?plan=pro',
    highlighted: true,
  },
  {
    id: 'agency',
    name: 'Agentur',
    price: '299 €',
    period: '/Monat',
    note: 'oder 2.990 € im Jahr',
    description: 'Für alle, die fremde Websites betreuen.',
    features: [
      '25 Projekte inklusive',
      'Voller Pro-Funktionsumfang je Projekt',
      'Erweiterbar um weitere 25 Projekte',
      'Zentrale Übersicht über alle Domains',
    ],
    cta: 'Agentur buchen',
    href: APP_URL + '/register?plan=agency',
  },
];

export default function PricingSection() {
  return (
    <section id="preise" className="bg-gray-50 py-20 scroll-mt-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

        <div className="text-center max-w-2xl mx-auto mb-14">
          <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Preise</span>
          <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mt-3 mb-4">
            Scannen ist kostenlos. Bezahlt wird erst das Beheben.
          </h2>
          <p className="text-gray-500 leading-relaxed">
            Du siehst zuerst, was auf deiner Website nicht stimmt – vollständig und ohne Zahlungsdaten.
            Erst wenn du die Befunde abstellen willst, wird ein Tarif fällig.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 items-stretch">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`relative flex flex-col rounded-2xl p-6 transition-shadow ${
                plan.highlighted
                  ? 'bg-white border-2 border-blue-600 shadow-xl'
                  : 'bg-white border border-gray-200 hover:shadow-md'
              }`}
            >
              {plan.highlighted && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-blue-600 text-white text-xs font-semibold px-3 py-1 rounded-full whitespace-nowrap">
                  Am häufigsten gewählt
                </div>
              )}

              <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
              <p className="text-sm text-gray-500 mt-1 mb-5 min-h-[40px]">{plan.description}</p>

              <div className="mb-1 flex items-baseline gap-1">
                <span className="text-4xl font-extrabold text-gray-900">{plan.price}</span>
                <span className="text-sm text-gray-500">{plan.period}</span>
              </div>
              <p className="text-xs text-gray-400 mb-6 min-h-[16px]">{plan.note ?? ''}</p>

              <ul className="space-y-3 mb-8 flex-1">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-sm text-gray-600">
                    <Check className="w-4 h-4 text-green-500 flex-shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href={plan.href}
                className={`inline-flex items-center justify-center gap-2 w-full font-semibold px-5 py-3 rounded-xl transition-colors ${
                  plan.highlighted
                    ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-100'
                    : 'bg-gray-50 hover:bg-gray-100 text-gray-700 border border-gray-200'
                }`}
              >
                {plan.cta}
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>

        <div className="mt-8 rounded-2xl bg-gray-900 text-white p-8 flex flex-col lg:flex-row lg:items-center gap-6">
          <div className="flex-1">
            <div className="inline-flex items-center gap-2 bg-white/10 rounded-full px-3 py-1 mb-3">
              <Sparkles className="w-3.5 h-3.5 text-orange-400" />
              <span className="text-xs font-semibold uppercase tracking-wide">Expert-Paket</span>
            </div>
            <h3 className="text-2xl font-bold mb-2">Wir überarbeiten deine Website selbst.</h3>
            <p className="text-gray-300 text-sm leading-relaxed max-w-2xl">
              Kein Selbermachen: Wir setzen die Befunde auf deiner Seite um und übergeben sie rechtssicher.
              Einmalig 3.990 € netto, danach 29 € im Monat für laufende Updates, damit es auch so bleibt.
            </p>
          </div>
          <a
            href="mailto:support@complyo.de?subject=Anfrage%20Expert-Paket"
            className="inline-flex items-center justify-center gap-2 bg-white text-gray-900 font-semibold px-6 py-3.5 rounded-xl hover:bg-gray-100 transition-colors flex-shrink-0"
          >
            Expert-Paket anfragen
            <ArrowRight className="w-4 h-4" />
          </a>
        </div>

        <p className="text-center text-xs text-gray-400 mt-6">
          Alle Preise zzgl. MwSt. · Abos monatlich kündbar · Zahlung per Karte oder SEPA-Lastschrift
        </p>
      </div>
    </section>
  );
}
