'use client';

import React from 'react';
import { Cookie, Scan, FileText, Bot, Shield, BarChart3 } from 'lucide-react';

const features = [
  {
    icon: Cookie,
    title: 'Cookie-Banner & Consent Management',
    description: 'DSGVO-konformer Cookie-Banner mit Google Consent Mode v2, TCF 2.2 und individuell anpassbarem Design.',
    color: 'from-sky-500 to-cyan-400',
    stats: [
      { label: 'Setup', value: '5 Minuten' },
      { label: 'Consent Rate', value: 'Ø 85%' }
    ]
  },
  {
    icon: Scan,
    title: 'Automatischer Website-Scanner',
    description: 'Scannt deine Website auf Cookies, Tracker und Datenschutz-Verstöße. Identifiziert Risiken automatisch.',
    color: 'from-violet-500 to-fuchsia-500',
    stats: [
      { label: 'Scan-Dauer', value: '< 30 Sek.' },
      { label: 'Prüfpunkte', value: '200+' }
    ]
  },
  {
    icon: FileText,
    title: 'Impressum & Datenschutz-Generator',
    description: 'Rechtssichere Texte für Impressum, Datenschutzerklärung und AGB. Immer aktuell bei Gesetzesänderungen.',
    color: 'from-emerald-500 to-lime-500',
    stats: [
      { label: 'Vorlagen', value: 'Anwalt geprüft' },
      { label: 'Updates', value: 'Automatisch' }
    ]
  },
  {
    icon: Bot,
    title: 'AI-gestützte Compliance-Analyse',
    description: 'Complyo AI analysiert deine Website und gibt konkrete Handlungsempfehlungen für rechtssicheren Betrieb.',
    color: 'from-orange-500 to-rose-500',
    stats: [
      { label: 'Empfehlungen', value: 'Personalisiert' },
      { label: 'Sprachen', value: 'DE + EN' }
    ]
  }
];

export default function ProductFeatures() {
  return (
    <section id="features" className="bg-white py-20 text-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Alle Compliance-Tools in einer Plattform</h2>
          <p className="text-lg text-slate-600 max-w-3xl mx-auto">
            Ein Dashboard für Cookie-Consent, DSGVO-Compliance, Rechtsdokumente und automatische Überwachung.
            Nie wieder Abmahnungen oder Bußgelder riskieren.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
          {features.map((feature) => (
            <div
              key={feature.title}
              className="rounded-3xl border border-slate-100 bg-slate-50 p-8 shadow-lg transition hover:border-slate-200"
            >
              <div className={`inline-flex items-center justify-center rounded-2xl bg-gradient-to-br ${feature.color} p-4 text-white mb-6 shadow-xl`}>
                <feature.icon className="h-6 w-6" />
              </div>
              <h3 className="text-2xl font-semibold mb-3">{feature.title}</h3>
              <p className="text-base text-slate-600 mb-6">{feature.description}</p>
              <div className="grid grid-cols-2 gap-4 text-sm text-slate-500">
                {feature.stats.map((stat) => (
                  <div key={stat.label} className="rounded-2xl border border-slate-100 p-4 bg-white">
                    <div className="text-lg font-semibold text-slate-900">{stat.value}</div>
                    <div className="text-xs uppercase tracking-[0.3em] text-slate-400">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="rounded-3xl border border-slate-100 bg-gradient-to-r from-cyan-500/10 to-slate-50 p-6 shadow-md">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-cyan-500" />
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-500">Abmahn-Schutz</p>
                <p className="text-lg font-semibold text-slate-900">Rechtssichere Compliance</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              Regelmäßige Updates bei Gesetzesänderungen. Anwaltlich geprüfte Vorlagen und automatische Anpassungen.
            </p>
          </div>
          <div className="rounded-3xl border border-slate-100 bg-gradient-to-r from-indigo-500/10 to-slate-50 p-6 shadow-md">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-6 h-6 text-indigo-500" />
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-500">Analytics</p>
                <p className="text-lg font-semibold text-slate-900">Consent-Statistiken & Reports</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              Detaillierte Auswertungen zu Consent-Raten, Cookie-Nutzung und Compliance-Status deiner Websites.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
