'use client';

import React from 'react';
import { Layers, Shield, Lock, Zap, Clock, HeadphonesIcon } from 'lucide-react';

const benefits = [
  {
    icon: Layers,
    title: 'Alles an einem Ort',
    description: 'Cookie-Banner, Scanner, Rechtsdokumente, Consent Mode und Monitoring in einem einzigen Dashboard.',
    color: 'from-slate-900 to-slate-900'
  },
  {
    icon: Shield,
    title: 'Rechtssicher & Anwalt geprüft',
    description: 'Alle Vorlagen und Funktionen werden regelmäßig von spezialisierten IT-Anwälten überprüft und aktualisiert.',
    color: 'from-cyan-500 to-blue-500'
  },
  {
    icon: Lock,
    title: 'Made in Germany / DSGVO',
    description: 'Hosting in Deutschland, keine US-Drittanbieter, 100% DSGVO-konform. Deine Daten bleiben in der EU.',
    color: 'from-emerald-500 to-teal-500'
  },
  {
    icon: Zap,
    title: 'AI-gestützte Analyse',
    description: 'Complyo AI scannt deine Website automatisch und gibt konkrete Optimierungsvorschläge für bessere Compliance.',
    color: 'from-fuchsia-500 to-orange-500'
  },
  {
    icon: Clock,
    title: 'Setup in 5 Minuten',
    description: 'Einfache Integration per Script-Tag oder Plugin. Kein Entwickler nötig, sofort einsatzbereit.',
    color: 'from-indigo-500 to-violet-500'
  },
  {
    icon: HeadphonesIcon,
    title: 'Persönlicher Support',
    description: 'Direkter Kontakt zu unserem Support-Team. Hilfe bei Integration, Konfiguration und rechtlichen Fragen.',
    color: 'from-yellow-500 to-amber-500'
  }
];

export default function BenefitsGrid() {
  return (
    <section className="bg-slate-950 py-20 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-sm uppercase tracking-[0.4em] text-white/60">All-in-One</p>
          <h2 className="text-4xl font-bold mt-4">Warum Unternehmen Complyo vertrauen</h2>
          <p className="text-lg text-white/70 max-w-3xl mx-auto mt-3">
            Nie wieder Sorgen um Cookie-Banner, DSGVO oder Abmahnungen. Wir kümmern uns um deine Compliance, 
            damit du dich auf dein Business konzentrieren kannst.
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
            <div className="text-5xl font-bold text-white">50.000€+</div>
            <p className="text-sm text-white/70">Durchschnittliche Ersparnis bei vermiedenen Bußgeldern</p>
            <p className="text-xs uppercase tracking-[0.4em] text-white/60">pro Jahr & Unternehmen</p>
          </div>
        </div>
      </div>
    </section>
  );
}
