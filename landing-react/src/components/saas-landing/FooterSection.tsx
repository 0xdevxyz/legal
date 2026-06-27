'use client';
import React from 'react';

export default function FooterSection() {
  return (
    <footer className="bg-gray-900 text-gray-400 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-10 mb-14">
          <div className="lg:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">C</span>
              </div>
              <span className="text-white font-bold text-xl">complyo</span>
            </div>
            <p className="text-sm leading-relaxed mb-5">
              Die KI-Compliance-Plattform für Websites. DSGVO, Cookie-Recht und Barrierefreiheit – automatisch und rechtssicher.
            </p>
            <a
              href="#waitlist"
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Auf Warteliste
            </a>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Rechtliches</h4>
            <ul className="space-y-2.5 text-sm">
              {[
                { label: 'Impressum', href: '/impressum' },
                { label: 'Datenschutz', href: '/datenschutz' },
                { label: 'Cookie-Richtlinie', href: '/cookie-richtlinie' },
                { label: 'AGB', href: '/agb' },
              ].map((l, i) => (
                <li key={i}><a href={l.href} className="hover:text-white transition-colors">{l.label}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="text-white font-semibold text-sm mb-4">Kontakt</h4>
            <ul className="space-y-2.5 text-sm">
              <li><a href="mailto:support@complyo.de" className="hover:text-white transition-colors">support@complyo.de</a></li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs">© {new Date().getFullYear()} Complyo. Alle Rechte vorbehalten.</p>
          <p className="text-xs">Made with ♥ in Germany · DSGVO-konform</p>
        </div>
      </div>
    </footer>
  );
}
