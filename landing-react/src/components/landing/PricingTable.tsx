'use client';

import React from 'react';
import { Sparkles, CreditCard, Shield } from 'lucide-react';

export default function PricingTable() {
  return (
    <section id="pricing" className="bg-slate-950 text-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">Preise</p>
          <h2 className="text-4xl sm:text-5xl font-bold mt-4">
            Ab 49€ / Monat für dein Creator Business
          </h2>
          <p className="mt-3 text-lg text-white/70 max-w-3xl mx-auto">
            Enthält Landingpage, Member-Bereich, Zahlungsabwicklung, E-Mail-Marketing, CRM, Automationen und Live-Support.
            Teste 14 Tage kostenfrei und tätige danach nur 49€ pro Monat.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-900/60 p-8 shadow-2xl">
            <div className="flex items-center gap-3 pb-6">
              <Sparkles className="w-8 h-8 text-cyan-400" />
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-white/60">Creator Plan</p>
                <p className="text-2xl font-semibold text-white">All-in-One</p>
              </div>
            </div>
            <div className="mb-6">
              <p className="text-5xl font-bold">49€</p>
              <p className="text-sm text-white/60">pro Monat • inkl. DSGVO + Hosting</p>
            </div>
            <ul className="space-y-4 text-sm text-white/80 mb-6">
              <li>✅ Unbegrenzte Kurse & Inhalte</li>
              <li>✅ Member-Bereich + Community</li>
              <li>✅ Automationen & alfi AI Copy</li>
              <li>✅ Terminbuchung & CRM</li>
              <li>✅ E-Mail-Marketing & Funnels</li>
              <li>✅ WhatsApp Support & Academy</li>
            </ul>
            <a
              href="https://alfima.io"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
            >
              Jetzt kostenfrei testen
              <Sparkles className="w-4 h-4" />
            </a>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 shadow-lg">
            <div className="flex items-center gap-3 pb-4">
              <CreditCard className="w-6 h-6 text-emerald-400" />
              <p className="text-sm uppercase tracking-[0.4em] text-white/60">Transaktionsgebühren</p>
            </div>
            <div className="text-3xl font-bold text-white mb-2">1,00 € + 4%</div>
            <p className="text-sm text-white/70 mb-6">
              Zusätzlich für digitale Produkte. Transparent, keine versteckten Wochen- oder Monatsgebühren.
            </p>
            <p className="text-xs text-white/60">
              *Bei Nutzung eigener Zahlungsanbieter entfällt die Zusatzgebühr.
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/20 to-slate-900/40 p-8 shadow-xl">
            <div className="flex items-center gap-3 pb-4">
              <Shield className="w-6 h-6 text-sky-400" />
              <p className="text-sm uppercase tracking-[0.4em] text-white/60">Sicherheit & Support</p>
            </div>
            <p className="text-lg font-semibold text-white mb-3">DSGVO, ISO & ePrivacy ready</p>
            <p className="text-sm text-white/70">
              Hosting in Deutschland, regelmäßige Updates, EU-konforme Sicherheitsmaßnahmen und persönlicher Support via WhatsApp & Onboarding Calls.
            </p>
            <div className="mt-6 rounded-2xl border border-white/20 bg-white/10 p-5 text-sm text-white/80">
              <p className="text-xs uppercase tracking-[0.4em] text-white/60">Onboarding</p>
              <p className="text-lg font-semibold text-white">1:1 Call inklusive</p>
              <p className="text-sm text-white/70">Strategie, Technik und Positionierung live besprechen.</p>
            </div>
          </div>
        </div>

        <div className="mt-10 text-center text-xs uppercase tracking-[0.4em] text-white/40">
          14 Tage kostenfrei • Jederzeit kündbar • DSGVO-konform
        </div>
      </div>
    </section>
  );
}
