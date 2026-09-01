'use client';
import React from 'react';
import { Logo } from '@/components/Logo';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.complyo.de';

export default function FooterSection() {
  return (
    <footer className="bg-gray-900 text-gray-400 pt-16 pb-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10 mb-14">
          <div className="lg:col-span-1">
            <div className="mb-4">
              <Logo size="sm" />
            </div>
            <p className="text-sm leading-relaxed mb-5">
              Die KI-Compliance-Plattform für Websites. DSGVO, Cookie-Recht und Barrierefreiheit – automatisch und rechtssicher.
            </p>
            <a
              href={`${APP_URL}/register?plan=free`}
              className="inline-flex items-center gap-2 bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Kostenlos starten
            </a>
          </div>

          <div>
            <h2 className="text-white font-semibold text-sm mb-4">Produkt</h2>
            <ul className="space-y-2.5 text-sm">
              {[
                { label: 'Preise', href: '/#preise' },
                { label: 'BFSG-Check', href: '/bfsg-check/' },
                { label: 'DSGVO-Check', href: '/dsgvo-website-check/' },
                { label: 'Barrierefreiheit testen', href: '/barrierefreiheit-website-testen/' },
                { label: 'Ratgeber', href: '/ratgeber/' },
                { label: 'Anmelden', href: `${APP_URL}/login` },
              ].map((l, i) => (
                <li key={i}><a href={l.href} className="hover:text-white transition-colors">{l.label}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-white font-semibold text-sm mb-4">Rechtliches</h2>
            <ul className="space-y-2.5 text-sm">
              {[
                { label: 'Impressum', href: '/impressum/' },
                { label: 'Datenschutz', href: '/datenschutz/' },
                { label: 'Cookie-Richtlinie', href: '/cookie-richtlinie/' },
                { label: 'AGB', href: '/agb/' },
              ].map((l, i) => (
                <li key={i}><a href={l.href} className="hover:text-white transition-colors">{l.label}</a></li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-white font-semibold text-sm mb-4">Kontakt</h2>
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
