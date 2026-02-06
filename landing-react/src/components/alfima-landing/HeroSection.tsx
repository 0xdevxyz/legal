'use client';

import React from 'react';
import { ArrowRight, Shield, Scan } from 'lucide-react';

const quickStats = [
  { label: 'Websites geschützt', value: '2.500+', detail: 'vertrauen auf Complyo' },
  { label: 'Compliance-Scans', value: '50.000+', detail: 'durchgeführt' },
  { label: 'Support', value: '24/7', detail: 'persönliche Beratung' }
];

const modules = [
  'Cookie-Banner',
  'DSGVO-Scanner',
  'Consent Mode v2',
  'Impressum-Generator',
  'AI-Compliance',
  'Datenschutz-Texte'
];

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-900 to-sky-900 text-white">
      <div
        className="absolute inset-0 opacity-40"
        style={{
          backgroundImage:
            'radial-gradient(circle at 20% 20%, rgba(255,255,255,0.2) 0, transparent 50%), radial-gradient(circle at 80% 0%, rgba(14,165,233,0.25) 0, transparent 40%)'
        }}
      />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white/80">
              <Shield className="w-4 h-4 text-white" />
              All-in-One Compliance Lösung
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
              DSGVO & Cookie-Compliance mit{' '}
              <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500 bg-clip-text text-transparent">
                nur einer Plattform
              </span>
            </h1>

            <p className="text-lg text-white/80 leading-relaxed max-w-2xl">
              Cookie-Banner, DSGVO-Scanner, Impressum-Generator, Consent Mode v2 und AI-gestützte 
              Compliance-Checks – alles zentral gesteuert. Die Complyo AI analysiert deine Website 
              automatisch und schlägt rechtssichere Optimierungen vor.
            </p>

            <div className="flex flex-wrap gap-3">
              {modules.map((module) => (
                <span
                  key={module}
                  className="rounded-full border border-white/30 px-4 py-1 text-sm text-white/80 backdrop-blur"
                >
                  {module}
                </span>
              ))}
            </div>

            <div className="flex flex-wrap gap-4">
              <a
                href="#pricing"
                className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-base font-semibold text-slate-950 transition hover:bg-slate-100 shadow-lg"
              >
                14 Tage kostenfrei testen
                <ArrowRight className="w-4 h-4" />
              </a>
              <a
                href="#features"
                className="inline-flex items-center gap-2 rounded-xl border border-white/40 px-6 py-3 text-base font-semibold text-white transition hover:border-white"
              >
                Website jetzt scannen
                <Scan className="w-4 h-4" />
              </a>
            </div>

            <div className="grid w-full grid-cols-2 sm:grid-cols-3 gap-4 text-sm text-white/80">
              {quickStats.map((stat) => (
                <div key={stat.label} className="rounded-2xl bg-white/10 px-4 py-3">
                  <div className="text-lg font-bold text-white">{stat.value}</div>
                  <div className="text-[10px] uppercase tracking-[0.3em] text-white/70">{stat.label}</div>
                  <p className="text-xs text-white/70">{stat.detail}</p>
                </div>
              ))}
            </div>

            <p className="text-sm text-white/70">
              Made in Germany. 100% DSGVO-konform. Persönlicher Support und regelmäßige 
              rechtliche Updates inklusive.
            </p>
          </div>

          <div className="relative">
            <div className="absolute -inset-2 rounded-3xl bg-gradient-to-br from-cyan-400/40 via-blue-500/40 to-violet-500/40 blur-3xl" />
            <div className="relative rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur">
              <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 text-white">
                <p className="text-xs uppercase tracking-[0.3em] text-white/50">Live Compliance Status</p>
                <div className="mt-4 space-y-4 text-left">
                  <div>
                    <p className="text-xs text-white/60">Cookie-Banner</p>
                    <div className="text-3xl font-bold text-emerald-400">✓ Aktiv</div>
                  </div>
                  <div>
                    <p className="text-xs text-white/60">DSGVO-Score</p>
                    <div className="text-3xl font-bold">98/100</div>
                  </div>
                  <div>
                    <p className="text-xs text-white/60">Consent Rate</p>
                    <div className="text-3xl font-bold">87%</div>
                  </div>
                </div>
                <div className="mt-6 rounded-2xl bg-white/10 px-4 py-3 text-sm text-white/80">
                  <p className="font-semibold">Complyo AI Empfehlung</p>
                  <p className="text-xs text-white/70">3 Optimierungen für bessere Consent-Rate</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
