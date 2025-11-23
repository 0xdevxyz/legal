'use client';

import React, { useState, useEffect } from 'react';
import { Cookie, Shield, CheckCircle, X, Settings } from 'lucide-react';
import { Logo } from './Logo';

/**
 * DSGVO-konformes Cookie-Banner mit Consent-Management
 * Showcase für Complyo's Cookie-Compliance
 */
export default function CookieBanner() {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
  const [consent, setConsent] = useState({
    necessary: true, // Always true, can't be disabled
    analytics: false,
    marketing: false
  });

  useEffect(() => {
    // Check if user has already given consent
    const savedConsent = localStorage.getItem('cookie-consent');
    if (!savedConsent) {
      // Delay banner appearance for better UX
      setTimeout(() => setIsVisible(true), 1000);
    } else {
      const parsed = JSON.parse(savedConsent);
      setConsent(parsed);
      initializeCookies(parsed);
    }
  }, []);

  const initializeCookies = (consentData: typeof consent) => {
    // Analytics (e.g., Google Analytics)
    if (consentData.analytics) {
      // Initialize GA4 here
      console.log('Analytics cookies enabled');
    }

    // Marketing (e.g., Facebook Pixel, LinkedIn)
    if (consentData.marketing) {
      console.log('Marketing cookies enabled');
    }
  };

  const handleAcceptAll = () => {
    const allConsent = {
      necessary: true,
      analytics: true,
      marketing: true
    };
    setConsent(allConsent);
    localStorage.setItem('cookie-consent', JSON.stringify(allConsent));
    localStorage.setItem('cookie-consent-date', new Date().toISOString());
    initializeCookies(allConsent);
    setIsVisible(false);
  };

  const handleAcceptNecessary = () => {
    const necessaryOnly = {
      necessary: true,
      analytics: false,
      marketing: false
    };
    setConsent(necessaryOnly);
    localStorage.setItem('cookie-consent', JSON.stringify(necessaryOnly));
    localStorage.setItem('cookie-consent-date', new Date().toISOString());
    initializeCookies(necessaryOnly);
    setIsVisible(false);
  };

  const handleSaveCustom = () => {
    localStorage.setItem('cookie-consent', JSON.stringify(consent));
    localStorage.setItem('cookie-consent-date', new Date().toISOString());
    initializeCookies(consent);
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div 
      className="fixed inset-0 z-[100] bg-black bg-opacity-50 backdrop-blur-sm flex items-end md:items-center justify-center p-4"
      role="dialog"
      aria-labelledby="cookie-banner-title"
      aria-describedby="cookie-banner-description"
    >
      <div className="bg-gray-900 border-2 border-blue-500 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-slide-up">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-900 to-purple-900 p-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Cookie className="w-8 h-8 text-yellow-400" aria-hidden="true" />
              <div>
                <h2 id="cookie-banner-title" className="text-2xl font-bold text-white">
                  Cookie-Einstellungen
                </h2>
                <p className="text-sm text-gray-300">
                  <Shield className="w-4 h-4 inline mr-1" aria-hidden="true" />
                  DSGVO & TTDSG konform
                </p>
              </div>
            </div>
            <button
              onClick={handleAcceptNecessary}
              className="text-gray-400 hover:text-white transition"
              aria-label="Banner schließen und nur notwendige Cookies akzeptieren"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p id="cookie-banner-description" className="text-gray-300 mb-6 text-lg">
            Wir verwenden Cookies, um Ihnen die bestmögliche Nutzererfahrung zu bieten. 
            Durch die Nutzung unserer Website stimmen Sie der Verwendung von Cookies zu.
          </p>

          {/* Quick Actions */}
          {!showDetails && (
            <div className="flex flex-col md:flex-row gap-4 mb-6">
              <button
                onClick={handleAcceptAll}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-xl transition shadow-lg hover:shadow-xl"
                aria-label="Alle Cookies akzeptieren"
              >
                ✓ Alle akzeptieren
              </button>
              <button
                onClick={handleAcceptNecessary}
                className="flex-1 bg-gray-700 hover:bg-gray-600 text-white font-bold py-4 px-6 rounded-xl transition"
                aria-label="Nur notwendige Cookies akzeptieren"
              >
                Nur notwendige
              </button>
              <button
                onClick={() => setShowDetails(!showDetails)}
                className="flex-1 bg-gray-800 hover:bg-gray-700 text-white font-bold py-4 px-6 rounded-xl transition flex items-center justify-center gap-2"
                aria-label="Cookie-Einstellungen anpassen"
              >
                <Settings className="w-5 h-5" aria-hidden="true" />
                Anpassen
              </button>
            </div>
          )}

          {/* Detailed Settings */}
          {showDetails && (
            <div className="space-y-4 mb-6">
              {/* Necessary Cookies */}
              <div className="bg-gray-800 p-5 rounded-xl border border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <CheckCircle className="w-5 h-5 text-green-400" aria-hidden="true" />
                      <h3 className="font-bold text-white text-lg">Notwendige Cookies</h3>
                      <span className="text-xs bg-green-600 text-white px-2 py-1 rounded-full">
                        Immer aktiv
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-3">
                      Diese Cookies sind für die Grundfunktionen der Website erforderlich 
                      (z.B. Sitzungsverwaltung, Sicherheit, Cookie-Einstellungen).
                    </p>
                    <p className="text-xs text-gray-500">
                      Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse)
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={true}
                    disabled
                    className="w-6 h-6 mt-1"
                    aria-label="Notwendige Cookies (immer aktiv)"
                  />
                </div>
              </div>

              {/* Analytics Cookies */}
              <div className="bg-gray-800 p-5 rounded-xl border border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-bold text-white text-lg mb-2">Analyse-Cookies</h3>
                    <p className="text-sm text-gray-400 mb-3">
                      Diese Cookies helfen uns, die Nutzung unserer Website zu verstehen 
                      und zu verbessern (z.B. Google Analytics, Hotjar).
                    </p>
                    <p className="text-xs text-gray-500">
                      Rechtsgrundlage: Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={consent.analytics}
                    onChange={(e) => setConsent({...consent, analytics: e.target.checked})}
                    className="w-6 h-6 mt-1 accent-blue-600 cursor-pointer"
                    aria-label="Analyse-Cookies aktivieren/deaktivieren"
                  />
                </div>
              </div>

              {/* Marketing Cookies */}
              <div className="bg-gray-800 p-5 rounded-xl border border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-bold text-white text-lg mb-2">Marketing-Cookies</h3>
                    <p className="text-sm text-gray-400 mb-3">
                      Diese Cookies werden für personalisierte Werbung verwendet 
                      (z.B. Facebook Pixel, LinkedIn Insight Tag).
                    </p>
                    <p className="text-xs text-gray-500">
                      Rechtsgrundlage: Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    checked={consent.marketing}
                    onChange={(e) => setConsent({...consent, marketing: e.target.checked})}
                    className="w-6 h-6 mt-1 accent-blue-600 cursor-pointer"
                    aria-label="Marketing-Cookies aktivieren/deaktivieren"
                  />
                </div>
              </div>

              {/* Save Custom Button */}
              <button
                onClick={handleSaveCustom}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-xl transition shadow-lg hover:shadow-xl"
                aria-label="Ausgewählte Cookie-Einstellungen speichern"
              >
                Auswahl speichern
              </button>
            </div>
          )}

          {/* Legal Links */}
          <div className="border-t border-gray-800 pt-4 flex flex-wrap gap-4 text-sm text-gray-400">
            <a 
              href="/datenschutz" 
              className="hover:text-blue-400 underline transition"
              aria-label="Datenschutzerklärung lesen"
            >
              Datenschutzerklärung
            </a>
            <a 
              href="/impressum" 
              className="hover:text-blue-400 underline transition"
              aria-label="Impressum lesen"
            >
              Impressum
            </a>
            <a 
              href="/cookie-richtlinie" 
              className="hover:text-blue-400 underline transition"
              aria-label="Cookie-Richtlinie lesen"
            >
              Cookie-Richtlinie
            </a>
          </div>

          {/* Complyo Badge */}
          <div className="mt-6 bg-gradient-to-r from-green-900 to-blue-900 p-4 rounded-xl border border-green-500">
            <div className="flex items-center gap-3">
              <Shield className="w-6 h-6 text-green-400" aria-hidden="true" />
              <div className="flex-1">
                <p className="text-sm font-bold text-white">
                  ✓ DSGVO & TTDSG konform
                </p>
                <div className="flex items-center gap-2 mt-1">
                  <p className="text-xs text-gray-300">
                    Powered by
                  </p>
                  <Logo size="sm" showText={true} variant="default" />
                  <p className="text-xs text-gray-300">
                    • Anwalt-geprüft
                  </p>
                </div>
              </div>
              <a 
                href="#" 
                className="text-xs text-blue-400 hover:underline"
                aria-label="Mehr über Complyo erfahren"
              >
                Mehr erfahren →
              </a>
            </div>
          </div>
        </div>
      </div>

      {/* Animation Styles */}
      <style jsx global>{`
        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(100px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slide-up {
          animation: slide-up 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}

