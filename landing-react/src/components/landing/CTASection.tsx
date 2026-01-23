'use client';

import React from 'react';
import { ArrowRight, MessagesSquare } from 'lucide-react';

export default function CTASection() {
  return (
    <section className="bg-gradient-to-br from-cyan-500 via-blue-600 to-violet-500 text-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center space-y-6">
          <div className="inline-flex items-center justify-center rounded-full bg-white/20 px-6 py-2 text-sm font-bold uppercase tracking-[0.4em]">
            14 Tage kostenfrei testen
          </div>
          <h2 className="text-4xl sm:text-5xl font-bold">
            Starte dein digitales Business ohne Technik-Chaos
          </h2>
          <p className="text-lg text-white/90 max-w-3xl mx-auto leading-relaxed">
            alfima begleitet dich vom ersten Kurs bis zum Launch deiner Community. Inklusive persönlicher
            WhatsApp-Begleitung, Academy 2.0 und Live-Support durch das Gründer-Team.
          </p>

          <div className="flex flex-wrap justify-center gap-4">
            <a
              href="#pricing"
              className="inline-flex items-center gap-2 rounded-full bg-white px-8 py-3 text-base font-semibold text-slate-900 shadow-xl transition hover:bg-white/90"
            >
              Kostenfrei starten
              <ArrowRight className="w-4 h-4" />
            </a>
            <a
              href="#faq"
              className="inline-flex items-center gap-2 rounded-full border border-white/70 px-8 py-3 text-base font-semibold text-white transition hover:border-white"
            >
              Live Walkthrough
              <MessagesSquare className="w-4 h-4" />
            </a>
          </div>

          <div className="flex flex-wrap justify-center gap-6 text-xs uppercase tracking-[0.4em] text-white/70">
            <span>Launch Templates</span>
            <span>Automationen + Funnels</span>
            <span>WhatsApp Support</span>
          </div>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-3">
          <div className="rounded-3xl border border-white/20 bg-white/10 p-6 backdrop-blur">
            <div className="text-3xl font-bold text-white">1:1</div>
            <p className="text-sm text-white/70">Onboarding Call mit dem Gründer-Team</p>
          </div>
          <div className="rounded-3xl border border-white/20 bg-white/10 p-6 backdrop-blur">
            <div className="text-3xl font-bold text-white">24/7</div>
            <p className="text-sm text-white/70">WhatsApp Support & Academy 2.0</p>
          </div>
          <div className="rounded-3xl border border-white/20 bg-white/10 p-6 backdrop-blur">
            <div className="text-3xl font-bold text-white">0€</div>
            <p className="text-sm text-white/70">Keine Setup-Kosten & keine Tool-Flut</p>
          </div>
        </div>
      </div>
    </section>
  );
}
