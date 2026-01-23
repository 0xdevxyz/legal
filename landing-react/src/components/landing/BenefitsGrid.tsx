'use client';

import React from 'react';
import { Layers, Users, Shield, Zap, Calendar, MessageSquare } from 'lucide-react';

const benefits = [
  {
    icon: Layers,
    title: 'Alles an einem Ort',
    description: 'Landingpage, Kursplattform, Mitgliederbereich, Terminbuchung, CRM und E-Mail-Marketing im selben Cockpit.',
    color: 'from-slate-900 to-slate-900'
  },
  {
    icon: Users,
    title: 'Social Proof & Academy',
    description: 'Über 1.000 Creator teilen Erfolge, wöchentliche LIVE-Calls und Fallstudien zeigen dir, was funktioniert.',
    color: 'from-cyan-500 to-blue-500'
  },
  {
    icon: Shield,
    title: 'Made in Germany / DSGVO',
    description: 'Hosting, Datenabo und Support komplett DSGVO-konform. Keine US-amerikanischen Drittanbieter nötig.',
    color: 'from-emerald-500 to-teal-500'
  },
  {
    icon: Zap,
    title: 'Automationen & AI',
    description: 'alfi AI schlägt Texte, E-Mails, Zahlungserinnerungen und Upsell-Pfade für dich vor.',
    color: 'from-fuchsia-500 to-orange-500'
  },
  {
    icon: Calendar,
    title: 'Launch in Minuten',
    description: 'Vorlagen, eingebettete Calendly-ähnliche Buchungssysteme und automatische Teilnehmerlisten beschleunigen deine Releases.',
    color: 'from-indigo-500 to-violet-500'
  },
  {
    icon: MessageSquare,
    title: 'WhatsApp-Support & Onboarding',
    description: '1:1 Onboarding Calls, persönlicher WhatsApp-Support und Schritt-für-Schritt Guides für jede Funktion.',
    color: 'from-yellow-500 to-amber-500'
  }
];

export default function BenefitsGrid() {
  return (
    <section className="bg-slate-950 py-20 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-sm uppercase tracking-[0.4em] text-white/60">All-in-One</p>
          <h2 className="text-4xl font-bold mt-4">Warum Creator alfima lieben</h2>
          <p className="text-lg text-white/70 max-w-3xl mx-auto mt-3">
            Nie wieder zehn Insellösungen. Wir kombinieren das Beste aus Kursplattform, Shop, Member-Bereich, E-Mail-Marketing und CRM in einem übersichtlichen Dash.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {benefits.map((benefit) => (
            <div
              key={benefit.title}
              className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-xl transition hover:border-white/50"
            >
              <div className={`mb-6 inline-flex items-center justify-center rounded-2xl bg-gradient-to-br ${benefit.color} p-4 text-white shadow-2xl`}>
                <benefit.icon className="w-6 h-6" />
              </div>
              <h3 className="text-xl font-semibold mb-2">{benefit.title}</h3>
              <p className="text-sm text-white/70 leading-relaxed">{benefit.description}</p>
            </div>
          ))}
        </div>

        <div className="mt-16 text-center">
          <div className="inline-flex flex-col gap-2 rounded-3xl bg-gradient-to-r from-cyan-500/10 to-blue-500/5 px-8 py-6 text-left shadow-2xl">
            <div className="text-5xl font-bold text-white">400+ €</div>
            <p className="text-sm text-white/70">Einsparung pro Monat im Vergleich zu zehn Einzeltools</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/60">Starter vs All-in-One</p>
          </div>
        </div>
      </div>
    </section>
  );
}
