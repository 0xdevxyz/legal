'use client';

import React from 'react';
import { BookOpenCheck, FileText, CalendarCheck, Mail, Sparkles, BarChart3 } from 'lucide-react';

const features = [
  {
    icon: BookOpenCheck,
    title: 'Online-Kurse & Mitgliederbereiche',
    description: 'Baue lesson-Pläne, Kapitel und Community-Feeds – alles in einem Editor mit Member-Only Zugriff.',
    color: 'from-sky-500 to-cyan-400',
    stats: [
      { label: 'Launch ready', value: '3 Klicks' },
      { label: 'Mitgliederfeedback', value: 'Live' }
    ]
  },
  {
    icon: FileText,
    title: 'E-Books, PDFs & Downloads',
    description: 'Stelle digitale Infoprodukte bereit, verteile Upsells und binde einfache Checkout-Seiten ein.',
    color: 'from-violet-500 to-fuchsia-500',
    stats: [
      { label: 'Dateiformate', value: 'PDF + ePub' },
      { label: 'Automatische Lieferung', value: 'Instant' }
    ]
  },
  {
    icon: CalendarCheck,
    title: 'Terminbuchung & Coachings',
    description: 'Verknüpfe Coaching-Zeiten, Zoom, Kalender-Sync und automatische Zahlungserinnerungen.',
    color: 'from-emerald-500 to-lime-500',
    stats: [
      { label: 'Kalender-Sync', value: 'Google + iCloud' },
      { label: 'Reminder', value: 'via SMS & E-Mail' }
    ]
  },
  {
    icon: Mail,
    title: 'E-Mail-Marketing & Automationen',
    description: 'Segmentiere Nutzer, baue Funnels auf und sende personalisierte Nachrichten mit AI-Text-Vorschlägen.',
    color: 'from-orange-500 to-rose-500',
    stats: [
      { label: 'Automations', value: '5+ Flows' },
      { label: 'Öffnungsrate', value: 'Ø 67%' }
    ]
  }
];

export default function ProductFeatures() {
  return (
    <section id="features" className="bg-white py-20 text-slate-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">Alle Tools, die dein Creator Business braucht</h2>
          <p className="text-lg text-slate-600 max-w-3xl mx-auto">
            Ein Dashboard statt zehn Insellösungen. Erstelle Inhalte, verkaufe Produkte, manage Community und E-Mail-Marketing
            ohne deinen Workflow zu verlassen.
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
              <Sparkles className="w-6 h-6 text-cyan-500" />
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-500">Künstliche Intelligenz</p>
                <p className="text-lg font-semibold text-slate-900">alfi AI schreibt Texte und Kampagnen</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              Interpretation deiner Zielgruppe, Copy-Vorschläge und Upsell-Pfade auf Knopfdruck.
            </p>
          </div>
          <div className="rounded-3xl border border-slate-100 bg-gradient-to-r from-indigo-500/10 to-slate-50 p-6 shadow-md">
            <div className="flex items-center gap-3">
              <BarChart3 className="w-6 h-6 text-indigo-500" />
              <div>
                <p className="text-sm uppercase tracking-wide text-slate-500">Insight-Center</p>
                <p className="text-lg font-semibold text-slate-900">Echtzeit-KPIs für Revenue & Lokale Trends</p>
              </div>
            </div>
            <p className="mt-4 text-sm text-slate-600">
              Behalte die Conversion-Rate, Wiederkaufrate und Art deiner digitalen Produkte im Blick.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
