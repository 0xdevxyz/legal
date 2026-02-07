'use client';

import React from 'react';
import { Shield, Zap, Building2, Crown, Check, FileText, Eye, BarChart3 } from 'lucide-react';

const getAppUrl = (path: string) => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://localhost:3000${path}`;
    }
  }
  return `https://app.complyo.tech${path}`;
};

/**
 * PricingTable - Flexibles 4-Säulen-Modell
 * Einzelne Säule: 19€/Monat
 * Alle 4 Säulen: 49€/Monat
 * Expertenservice: 2.990€ + 39€/Monat
 */
export default function PricingTable() {
  const pillars = [
    { name: 'Cookie & DSGVO', icon: Shield },
    { name: 'Barrierefreiheit', icon: Eye },
    { name: 'Rechtliche Texte', icon: FileText },
    { name: 'Monitoring', icon: BarChart3 },
  ];

  return (
    <section id="pricing" className="bg-slate-950 text-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-xs uppercase tracking-[0.4em] text-white/60">Preise</p>
          <h2 className="text-4xl sm:text-5xl font-bold mt-4">
            Flexibel ab 19€ / Monat
          </h2>
          <p className="mt-3 text-lg text-white/70 max-w-3xl mx-auto">
            Wählen Sie einzelne Module oder das komplette Paket mit allen 4 Säulen.
            Teste 14 Tage kostenfrei mit vollem Funktionsumfang.
          </p>
        </div>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Einzelmodul */}
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-slate-900/80 to-slate-900/60 p-8 shadow-2xl">
            <div className="flex items-center gap-3 pb-6">
              <Shield className="w-8 h-8 text-cyan-400" />
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-white/60">Einzelmodul</p>
                <p className="text-2xl font-semibold text-white">1 Säule nach Wahl</p>
              </div>
            </div>
            <div className="mb-6">
              <p className="text-5xl font-bold">19€</p>
              <p className="text-sm text-white/60">pro Monat • 1 Säule inklusive</p>
            </div>
            <div className="mb-4">
              <p className="text-sm text-white/60 mb-2">Wählen Sie eine Säule:</p>
              <div className="space-y-2">
                {pillars.map((p, i) => (
                  <div key={i} className="flex items-center gap-2 text-white/80 text-sm">
                    <p.icon className="w-4 h-4 text-cyan-400" />
                    <span>{p.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <ul className="space-y-3 text-sm text-white/80 mb-6">
              <li>✅ KI-generierte Lösungen</li>
              <li>✅ Automatischer Scanner</li>
              <li>✅ E-Mail Support</li>
            </ul>
            <a
              href={getAppUrl('/register?plan=single')}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-slate-100"
            >
              Modul wählen
              <Shield className="w-4 h-4" />
            </a>
          </div>

          {/* Komplett-Paket */}
          <div className="rounded-3xl border-2 border-cyan-500 bg-gradient-to-br from-cyan-500/20 to-slate-900/60 p-8 shadow-2xl relative">
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 rounded-full bg-cyan-500 px-4 py-1 text-xs font-bold uppercase tracking-wider text-white">
              Beliebt
            </div>
            <div className="flex items-center gap-3 pb-6">
              <Zap className="w-8 h-8 text-cyan-400" />
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-white/60">Komplett-Paket</p>
                <p className="text-2xl font-semibold text-white">Alle 4 Säulen</p>
              </div>
            </div>
            <div className="mb-6">
              <p className="text-5xl font-bold">49€</p>
              <p className="text-sm text-white/60">pro Monat • Sie sparen 27€</p>
            </div>
            <div className="mb-4">
              <p className="text-sm text-cyan-400 mb-2">Alle 4 Säulen inklusive:</p>
              <div className="grid grid-cols-2 gap-2">
                {pillars.map((p, i) => (
                  <div key={i} className="flex items-center gap-2 text-white/90 text-sm">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>{p.name}</span>
                  </div>
                ))}
              </div>
            </div>
            <ul className="space-y-3 text-sm text-white/80 mb-6">
              <li>✅ Unbegrenzte Analysen</li>
              <li>✅ eRecht24 Integration</li>
              <li>✅ Priority Support</li>
              <li>✅ API-Zugang</li>
            </ul>
            <a
              href={getAppUrl('/register?plan=complete')}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-cyan-500 px-4 py-3 text-sm font-semibold text-white transition hover:bg-cyan-600"
            >
              Jetzt starten
              <Zap className="w-4 h-4" />
            </a>
          </div>

          {/* Expertenservice */}
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-indigo-500/20 to-slate-900/40 p-8 shadow-xl">
            <div className="flex items-center gap-3 pb-6">
              <Crown className="w-8 h-8 text-yellow-400" />
              <div>
                <p className="text-xs uppercase tracking-[0.4em] text-white/60">Expertenservice</p>
                <p className="text-2xl font-semibold text-white">Wir setzen um</p>
              </div>
            </div>
            <div className="mb-6">
              <p className="text-3xl font-bold">2.990€</p>
              <p className="text-sm text-white/60">einmalig + 39€/Monat</p>
            </div>
            <ul className="space-y-3 text-sm text-white/80 mb-6">
              <li>✅ Vollständige Umsetzung durch Experten</li>
              <li>✅ WCAG 2.1 AA Zertifizierung</li>
              <li>✅ Persönlicher Ansprechpartner</li>
              <li>✅ Laufende Updates bei Gesetzesänderungen</li>
              <li>✅ SLA & Uptime Garantie</li>
              <li>✅ Priority Support</li>
            </ul>
            <a
              href="mailto:expert@complyo.tech"
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl border border-white/30 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
            >
              Beratung anfragen
              <Building2 className="w-4 h-4" />
            </a>
          </div>
        </div>

        <div className="mt-10 text-center text-xs uppercase tracking-[0.4em] text-white/40">
          14 Tage kostenfrei • Jederzeit kündbar • Made in Germany
        </div>
      </div>
    </section>
  );
}
