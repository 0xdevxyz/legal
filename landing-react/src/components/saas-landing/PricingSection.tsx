'use client';
import React, { useState } from 'react';
import { Check, Zap, Crown, ArrowRight } from 'lucide-react';

const getAppUrl = (path: string) => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') return `http://localhost:3000${path}`;
  }
  return `https://app.complyo.de${path}`;
};

export default function PricingSection() {
  const [annual, setAnnual] = useState(false);

  const plans = [
    {
      name: 'Starter',
      icon: Zap,
      price: annual ? 0 : 0,
      period: 'kostenlos',
      description: 'Perfekt zum Einstieg und Testen',
      highlight: false,
      cta: 'Kostenlos starten',
      ctaUrl: '/register?plan=free',
      features: [
        '1 Website scannen',
        'Basis-Compliance-Report',
        'Impressum & Datenschutz Check',
        'Cookie-Erkennung',
        'E-Mail Support',
      ],
      notIncluded: [
        'KI-generierte Fixes',
        'Automatische Rechtstexte',
        'WCAG 2.1 Vollprüfung',
      ],
    },
    {
      name: 'Pro',
      icon: Crown,
      price: annual ? 39 : 49,
      period: '/Monat',
      sub: annual ? 'zzgl. MwSt. • jährlich' : 'zzgl. MwSt.',
      description: 'Alles für professionelle Compliance',
      highlight: true,
      badge: 'Beliebteste Wahl',
      cta: 'Jetzt Pro starten',
      ctaUrl: '/register?plan=pro',
      features: [
        'Unbegrenzte Websites',
        'Alle 4 Compliance-Module',
        'KI-generierte Code-Fixes',
        'KI-Rechtstexte (DSGVO, AGB, Impressum)',
        'WCAG 2.1 AA Vollprüfung',
        'Cookie Consent Manager (TCF 2.2)',
        'Rechtliches Monitoring & Alerts',
        'Priority Support',
      ],
    },
    {
      name: 'Expert',
      icon: Crown,
      price: 2990,
      period: 'einmalig',
      sub: '+ 39€/Monat danach',
      description: 'Wir übernehmen alles für Sie',
      highlight: false,
      cta: 'Beratung anfragen',
      ctaUrl: '/contact?service=expert',
      features: [
        'Alles aus Pro',
        'Vollständige Umsetzung durch Experten',
        'WCAG 2.1 AA Zertifizierung',
        'Persönlicher Ansprechpartner',
        'Individuelle Workshops & Schulungen',
        'Laufende Updates bei Gesetzesänderungen',
        'SLA-Garantie',
      ],
    },
  ];

  return (
    <section className="bg-white py-24" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-14">
          <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Pricing</p>
          <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-4">
            Flexible pricing for every team
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto mb-8">
            Starten Sie kostenlos und skalieren Sie mit Ihren Anforderungen. Kein Risiko, jederzeit kündbar.
          </p>
          {/* Annual Toggle */}
          <div className="inline-flex items-center gap-3 bg-gray-100 rounded-full px-2 py-2">
            <button onClick={() => setAnnual(false)} className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${!annual ? 'bg-white shadow text-gray-900' : 'text-gray-500'}`}>Monatlich</button>
            <button onClick={() => setAnnual(true)} className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${annual ? 'bg-white shadow text-gray-900' : 'text-gray-500'}`}>Jährlich</button>
            {annual && <span className="text-xs font-semibold text-green-600 bg-green-100 px-2.5 py-1 rounded-full">-20%</span>}
          </div>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-5xl mx-auto items-start">
          {plans.map((plan, i) => (
            <div key={i} className={`relative rounded-2xl p-8 border transition-all ${
              plan.highlight
                ? 'bg-blue-600 border-blue-500 shadow-2xl shadow-blue-200 scale-105 text-white'
                : 'bg-white border-gray-200 shadow-sm hover:shadow-md'
            }`}>
              {plan.badge && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-orange-400 to-yellow-400 text-gray-900 text-xs font-bold px-5 py-1.5 rounded-full shadow">
                    ⭐ {plan.badge}
                  </span>
                </div>
              )}

              <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${plan.highlight ? 'bg-white/20' : 'bg-blue-50'}`}>
                <plan.icon className={`w-5 h-5 ${plan.highlight ? 'text-white' : 'text-blue-600'}`} />
              </div>

              <h3 className={`font-heading text-xl font-extrabold mb-1 ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>{plan.name}</h3>
              <p className={`text-sm mb-5 ${plan.highlight ? 'text-blue-100' : 'text-gray-500'}`}>{plan.description}</p>

              <div className="mb-6">
                <div className="flex items-baseline gap-1.5">
                  {plan.name === 'Expert' ? (
                    <span className={`text-4xl font-extrabold ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>2.990€</span>
                  ) : (
                    <>
                      <span className={`text-4xl font-extrabold ${plan.highlight ? 'text-white' : 'text-gray-900'}`}>{plan.price}€</span>
                      <span className={`text-sm ${plan.highlight ? 'text-blue-200' : 'text-gray-500'}`}>{plan.period}</span>
                    </>
                  )}
                </div>
                {plan.sub && <p className={`text-xs mt-1 ${plan.highlight ? 'text-blue-200' : 'text-gray-400'}`}>{plan.sub}</p>}
              </div>

              <ul className="space-y-2.5 mb-8">
                {plan.features.map((f, j) => (
                  <li key={j} className="flex items-start gap-2.5">
                    <Check className={`w-4 h-4 flex-shrink-0 mt-0.5 ${plan.highlight ? 'text-green-300' : 'text-green-500'}`} />
                    <span className={`text-sm ${plan.highlight ? 'text-blue-50' : 'text-gray-600'}`}>{f}</span>
                  </li>
                ))}
                {plan.notIncluded?.map((f, j) => (
                  <li key={j} className="flex items-start gap-2.5 opacity-40">
                    <span className="w-4 h-4 flex-shrink-0 mt-0.5 text-center text-gray-400 text-xs">✕</span>
                    <span className="text-sm text-gray-500">{f}</span>
                  </li>
                ))}
              </ul>

              <a href={getAppUrl(plan.ctaUrl)} className={`flex items-center justify-center gap-2 w-full py-3 rounded-xl font-semibold text-sm transition-all ${
                plan.highlight
                  ? 'bg-white text-blue-700 hover:bg-blue-50 shadow-lg'
                  : plan.name === 'Expert'
                    ? 'bg-gray-900 text-white hover:bg-gray-800'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
              }`}>
                {plan.cta} <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          ))}
        </div>

        <p className="text-center text-sm text-gray-400 mt-10">
          💳 Sichere Zahlung via Stripe &nbsp;·&nbsp; 🔒 DSGVO-konform &nbsp;·&nbsp; ✓ Jederzeit kündbar
        </p>
      </div>
    </section>
  );
}
