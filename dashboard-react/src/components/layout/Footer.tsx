'use client';

import React, { useState } from 'react';
import { Shield, Cookie, FileText, Mail, ExternalLink } from 'lucide-react';
import { Logo } from '@/components/Logo';
import dynamic from 'next/dynamic';

// Dynamically import CookieConsentModal to avoid SSR issues
const CookieConsentModal = dynamic(
  () => import('@/components/dashboard/CookieConsentModal').then(mod => mod.CookieConsentModal),
  { ssr: false }
);

export const Footer: React.FC = () => {
  const [showCookieModal, setShowCookieModal] = useState(false);

  const handleOpenCookieSettings = () => {
    setShowCookieModal(true);
  };

  return (
    <>
      <footer className="glass-strong border-t border-white/10 mt-20">
        <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Company Info */}
            <div className="col-span-1 md:col-span-1">
              <Logo size="md" />
              <p className="text-zinc-400 text-sm mt-4">
                Ihre KI-gestützte Compliance-Plattform für DSGVO, BFSG & TTDSG.
              </p>
              <div className="flex items-center gap-2 mt-4">
                <Shield className="w-4 h-4 text-green-400" />
                <span className="text-xs text-zinc-500">Gehostet in Deutschland</span>
              </div>
            </div>

            {/* Legal Links */}
            <div>
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                Rechtliches
              </h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="/privacy"
                    className="text-zinc-400 hover:text-white text-sm transition-colors flex items-center gap-2"
                  >
                    <Shield className="w-3 h-3" />
                    Datenschutzerklärung
                  </a>
                </li>
                <li>
                  <button
                    onClick={handleOpenCookieSettings}
                    className="text-zinc-400 hover:text-white text-sm transition-colors flex items-center gap-2"
                  >
                    <Cookie className="w-3 h-3" />
                    Cookie-Einstellungen
                  </button>
                </li>
                <li>
                  <a
                    href="/impressum"
                    className="text-zinc-400 hover:text-white text-sm transition-colors flex items-center gap-2"
                  >
                    <FileText className="w-3 h-3" />
                    Impressum
                  </a>
                </li>
                <li>
                  <a
                    href="/agb"
                    className="text-zinc-400 hover:text-white text-sm transition-colors flex items-center gap-2"
                  >
                    <FileText className="w-3 h-3" />
                    AGB
                  </a>
                </li>
              </ul>
            </div>

            {/* Resources */}
            <div>
              <h3 className="text-white font-semibold mb-4">Ressourcen</h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="https://api.complyo.tech/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white text-sm transition-colors"
                  >
                    API-Dokumentation
                  </a>
                </li>
                <li>
                  <a
                    href="mailto:support@complyo.tech"
                    className="text-zinc-400 hover:text-white text-sm transition-colors"
                  >
                    Support
                  </a>
                </li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <Mail className="w-4 h-4" />
                Kontakt
              </h3>
              <ul className="space-y-2">
                <li>
                  <a
                    href="mailto:contact@complyo.tech"
                    className="text-zinc-400 hover:text-white text-sm transition-colors"
                  >
                    contact@complyo.tech
                  </a>
                </li>
                <li>
                  <a
                    href="mailto:privacy@complyo.tech"
                    className="text-zinc-400 hover:text-white text-sm transition-colors"
                  >
                    Datenschutz-Anfragen
                  </a>
                </li>
                <li className="pt-4">
                  <a
                    href="https://github.com/complyo"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-zinc-400 hover:text-white text-sm transition-colors flex items-center gap-2"
                  >
                    GitHub
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-zinc-500 text-sm">
              © {new Date().getFullYear()} Complyo.tech. Alle Rechte vorbehalten.
            </p>
            <div className="flex items-center gap-4 text-zinc-500 text-xs">
              <span>Made with ❤️ in Deutschland</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Shield className="w-3 h-3 text-green-400" />
                DSGVO-konform
              </span>
            </div>
          </div>
        </div>
      </footer>

      {/* Cookie Consent Modal */}
      {showCookieModal && (
        <CookieConsentModal
          onAccept={() => setShowCookieModal(false)}
          onDecline={() => setShowCookieModal(false)}
        />
      )}
    </>
  );
};

export default Footer;

