'use client';
import React, { useState, useEffect } from 'react';
import { Menu, X } from 'lucide-react';
import { Logo } from '@/components/Logo';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.complyo.de';

// "Preise" ist vorerst raus. Der Anker /#preise zeigte auf die Preistabelle
// der alten Startseite; seit dort die Early-Access-Seite steht, ginge er ins
// Leere. Auf /produkt umzubiegen waere schlimmer: dort stehen die Buchen-
// Knoepfe, und die fuehren mit Stripe im Testmodus in einen Checkout, der
// echte Karten ablehnt. Zurueck, sobald der Verkauf offen ist.
const LINKS = [
  { label: 'BFSG-Check', href: '/bfsg-check/' },
  { label: 'DSGVO-Check', href: '/dsgvo-website-check/' },
  { label: 'Barrierefreiheit', href: '/barrierefreiheit-website-testen/' },
  { label: 'Ratgeber', href: '/ratgeber/' },
];

export default function NavBar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/95 backdrop-blur-md shadow-sm border-b border-gray-100' : 'bg-white'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <a href="/" className="flex items-center flex-shrink-0" aria-label="complyo — zur Startseite">
            <Logo size="sm" variant="light" />
          </a>

          <div className="hidden lg:flex items-center gap-7">
            {LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="hidden lg:flex items-center gap-4">
            <a href={`${APP_URL}/login`} className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors">
              Anmelden
            </a>
            <a
              href="/#anmeldung"
              className="text-sm bg-blue-700 hover:bg-blue-800 text-white font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              Platz sichern
            </a>
          </div>

          <button
            className="lg:hidden p-2 text-gray-600"
            onClick={() => setOpen(!open)}
            aria-label={open ? 'Menü schließen' : 'Menü öffnen'}
            aria-expanded={open}
            aria-controls="mobile-menue"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>

        {(
          <div
            id="mobile-menue"
            hidden={!open}
            className="lg:hidden border-t border-gray-100 py-4 space-y-1"
          >
            {LINKS.map((link) => (
              <a
                key={link.href}
                href={link.href}
                onClick={() => setOpen(false)}
                className="block px-2 py-2 text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
              >
                {link.label}
              </a>
            ))}
            <div className="pt-3 mt-2 border-t border-gray-100 space-y-2">
              <a
                href={`${APP_URL}/login`}
                onClick={() => setOpen(false)}
                className="block px-2 py-2 text-sm font-medium text-gray-600"
              >
                Anmelden
              </a>
              <a
                href="/#anmeldung"
                onClick={() => setOpen(false)}
                className="block text-sm text-center bg-blue-600 text-white font-semibold rounded-lg px-4 py-2.5"
              >
                Platz sichern
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
