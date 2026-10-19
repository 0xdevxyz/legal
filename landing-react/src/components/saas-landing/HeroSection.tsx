'use client';
import React from 'react';
import { ArrowRight, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';
import Erklaervideo from '@/components/Erklaervideo';


export default function HeroSection() {
  return (
    <section className="relative bg-nacht-950 pt-24 pb-16 overflow-hidden">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-bl from-akzent-800/40 via-akzent-900/10 to-transparent rounded-full blur-3xl opacity-70 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-nacht-800 via-nacht-900 to-transparent rounded-full blur-3xl opacity-60 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[580px]">

          <div>
            <div className="inline-flex items-center gap-2 bg-akzent-400/10 border border-akzent-400/30 rounded-full px-4 py-1.5 mb-6">
              <ShieldCheck className="w-4 h-4 text-akzent-300" />
              <span className="text-xs font-semibold text-akzent-300 uppercase tracking-wide">DSGVO · WCAG · Cookie Compliance</span>
            </div>

            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-50 leading-[1.1] mb-6">
              Websites{' '}
              <span>prüfen und reparieren</span>{' '}
              mit{' '}
              <span className="whitespace-nowrap">
                <span className="relative inline-block">
                  <span className="text-akzent-400">KI</span>
                  <span className="absolute -bottom-1 left-0 right-0 h-1 bg-akzent-400/40 rounded-full" />
                </span>
                &#8209;Compliance
              </span>
            </h1>

            <p className="text-lg text-gray-400 mb-8 leading-relaxed max-w-xl">
              Complyo scannt und analysiert deine Website auf DSGVO-, Cookie- und Barrierefreiheitsprobleme – und liefert konkrete Lösungsvorschläge, die du direkt umsetzen kannst.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 mb-8 text-sm">
              {['Kostenloser Website-Scan', 'Ein Fix gratis', 'Keine Kreditkarte nötig'].map((item, i) => (
                <div key={i} className="flex items-center gap-1.5 text-gray-400">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <a href="#scanner" className="inline-flex items-center justify-center gap-2 bg-akzent-400 hover:bg-akzent-500 text-gray-900 font-semibold px-6 py-3.5 rounded-xl transition-colors shadow-md shadow-akzent-900/50">
                Website kostenlos scannen
                <ArrowRight className="w-4 h-4" />
              </a>
              <a href="#preise" className="inline-flex items-center justify-center gap-2 bg-nacht-800 hover:bg-nacht-700 text-gray-200 font-semibold px-6 py-3.5 rounded-xl border border-nacht-700 transition-colors">
                Preise ansehen
              </a>
            </div>

            <div className="mt-10 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-gray-400">
              <span className="inline-flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-akzent-400" aria-hidden="true" />
                Server und Daten in Deutschland
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Zap className="w-4 h-4 text-akzent-400" />
                Ergebnis in unter 60 Sekunden
              </span>
              <span className="inline-flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                DSGVO, Cookies, Barrierefreiheit und Rechtstexte in einem Scan
              </span>
            </div>
          </div>

          <div className="relative flex justify-center lg:justify-end">
            <div className="relative w-full max-w-[520px]">
              <div className="absolute inset-0 bg-gradient-to-br from-akzent-500 to-akzent-800 rounded-3xl blur-2xl opacity-30 scale-95" />

              <Erklaervideo />

              <div className="absolute -bottom-3 -left-3 bg-nacht-800 rounded-xl shadow-lg border border-nacht-700 px-4 py-2.5 flex items-center gap-2.5">
                <div className="w-8 h-8 bg-green-950/60 rounded-lg flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-green-400" />
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-50">DSGVO und TDDDG geprüft</p>
                  <p className="text-xs text-gray-400">Im Browser gemessen</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
