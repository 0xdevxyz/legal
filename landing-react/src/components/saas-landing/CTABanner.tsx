'use client';
import React from 'react';
import { ArrowRight, ShieldCheck } from 'lucide-react';

export default function CTABanner() {
  return (
    <section className="bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-700 py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <div className="inline-flex items-center gap-2 bg-white/10 border border-white/20 rounded-full px-4 py-1.5 mb-6">
          <ShieldCheck className="w-4 h-4 text-white" />
          <span className="text-xs font-semibold text-white uppercase tracking-wide">Jetzt starten</span>
        </div>

        <h2 className="font-heading text-3xl sm:text-4xl lg:text-5xl font-extrabold text-white mb-5 leading-tight">
          Starten Sie heute mit<br />rechtssicherer Compliance
        </h2>
        <p className="text-lg text-blue-100 mb-10 max-w-2xl mx-auto">
          Keine Kreditkarte nötig. Kostenlos starten, in Minuten einsatzbereit. Über 2.500 Websites vertrauen bereits auf Complyo.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a href="https://app.complyo.de/register" className="inline-flex items-center justify-center gap-2 bg-white hover:bg-gray-50 text-blue-700 font-bold px-8 py-4 rounded-xl transition-all shadow-xl text-sm">
            Kostenlos starten
            <ArrowRight className="w-4 h-4" />
          </a>
          <a href="https://app.complyo.de/demo" className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 border border-white/30 text-white font-semibold px-8 py-4 rounded-xl transition-all text-sm">
            Live-Demo ansehen
          </a>
        </div>

        <p className="text-blue-200 text-xs mt-6">
          ✓ Keine Kreditkarte &nbsp;·&nbsp; ✓ 14 Tage kostenlos &nbsp;·&nbsp; ✓ DSGVO-konform
        </p>
      </div>
    </section>
  );
}
