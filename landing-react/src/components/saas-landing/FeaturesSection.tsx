'use client';
import React from 'react';
import { CheckCircle2, ArrowRight } from 'lucide-react';

export default function FeaturesSection() {
  return (
    <section className="bg-white py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-28">

        {/* Block 1: Text links, Mock rechts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div>
            <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Automatische Prüfung</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-5 leading-tight">
              Features that simplify<br />your compliance workflows
            </h2>
            <p className="text-lg text-gray-500 mb-8 leading-relaxed">
              Complyo scannt Ihre Website vollautomatisch auf alle rechtlichen Anforderungen – DSGVO, Cookie-Recht, Barrierefreiheit und mehr. In Minuten, nicht Wochen.
            </p>
            <ul className="space-y-3 mb-8">
              {[
                'Über 200 Prüfpunkte in einem Scan',
                'KI-Priorisierung nach Risiko und Dringlichkeit',
                'Verständliche Erklärungen und Lösungsvorschläge',
                'Automatische Rescan-Erkennung nach Änderungen',
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-600 text-sm">{item}</span>
                </li>
              ))}
            </ul>
            <a href="https://app.complyo.de/register" className="inline-flex items-center gap-2 text-blue-600 font-semibold text-sm hover:gap-3 transition-all">
              Jetzt kostenlos testen <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          {/* Mock UI */}
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-3xl blur-2xl opacity-60 scale-95" />
            <div className="relative bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              <div className="bg-blue-600 px-5 py-3 flex items-center justify-between">
                <span className="text-white text-sm font-semibold">Scan läuft – complyo.de</span>
                <span className="text-blue-200 text-xs">92% abgeschlossen</span>
              </div>
              <div className="p-5 space-y-3">
                {[
                  { label: 'Datenschutzerklärung', status: 'OK', color: 'text-green-600 bg-green-50' },
                  { label: 'Impressum vollständig', status: 'OK', color: 'text-green-600 bg-green-50' },
                  { label: 'Cookie Consent fehlt', status: 'Kritisch', color: 'text-red-600 bg-red-50' },
                  { label: 'Alt-Texte bei Bildern', status: '3 fehlen', color: 'text-orange-600 bg-orange-50' },
                  { label: 'Kontrastprüfung', status: '2 Fehler', color: 'text-yellow-600 bg-yellow-50' },
                  { label: 'AGB & Widerruf', status: 'OK', color: 'text-green-600 bg-green-50' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-2.5">
                    <span className="text-sm text-gray-700">{item.label}</span>
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${item.color}`}>{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Block 2: Mock links, Text rechts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Code-Fix Mock */}
          <div className="relative order-2 lg:order-1">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-50 to-pink-50 rounded-3xl blur-2xl opacity-60 scale-95" />
            <div className="relative bg-gray-900 rounded-2xl shadow-xl overflow-hidden">
              <div className="px-5 py-3 border-b border-gray-700 flex items-center gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-500" />
                <span className="ml-2 text-gray-400 text-xs">KI-Fix – header.html</span>
              </div>
              <div className="p-5 font-mono text-sm space-y-1.5">
                <div className="text-gray-500 text-xs mb-3">// Complyo KI-generierter Fix</div>
                <div><span className="text-red-400">- &lt;img src="logo.png"&gt;</span></div>
                <div><span className="text-green-400">+ &lt;img src="logo.png"</span></div>
                <div className="pl-4"><span className="text-green-400">alt="Complyo Logo"</span></div>
                <div className="pl-4"><span className="text-green-400">role="img"&gt;</span></div>
                <div className="mt-3 text-gray-500 text-xs">// WCAG 2.1 – Kriterium 1.1.1</div>
                <div className="mt-2"><span className="text-purple-400">aria-label</span><span className="text-white">=</span><span className="text-yellow-300">"Navigation öffnen"</span></div>
              </div>
              <div className="px-5 py-3 bg-green-900/30 border-t border-green-700/30 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-green-400" />
                <span className="text-green-400 text-xs font-semibold">Fix validiert – direkt einspielen</span>
              </div>
            </div>
          </div>

          <div className="order-1 lg:order-2">
            <p className="text-sm font-semibold text-purple-600 uppercase tracking-widest mb-3">KI-gestützte Lösungen</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-5 leading-tight">
              Gain smarter insights<br />with AI-powered fixes
            </h2>
            <p className="text-lg text-gray-500 mb-8 leading-relaxed">
              Statt langer Agentur-Wartezeiten erhalten Sie sofort fertige Code-Fixes – direkt in Ihre Dateien einspielen. KI-generiert, rechtssicher, sofort verfügbar.
            </p>
            <ul className="space-y-3 mb-8">
              {[
                'Copy-Paste Code für jeden Fehler',
                'Genauer Dateipfad und Zeilennummer',
                'Schritt-für-Schritt Anleitungen für Laien',
                'Rechtliche Begründung für jeden Fix',
              ].map((item, i) => (
                <li key={i} className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-purple-500 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-600 text-sm">{item}</span>
                </li>
              ))}
            </ul>
            <a href="https://app.complyo.de/register" className="inline-flex items-center gap-2 text-purple-600 font-semibold text-sm hover:gap-3 transition-all">
              KI-Fixes ausprobieren <ArrowRight className="w-4 h-4" />
            </a>
          </div>
        </div>

      </div>
    </section>
  );
}
