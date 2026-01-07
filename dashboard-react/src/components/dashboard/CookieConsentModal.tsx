'use client';

import React, { useState, useEffect } from 'react';
import { Cookie, Shield, X, CheckCircle } from 'lucide-react';

interface CookieConsentModalProps {
  onAccept?: () => void;
  onDecline?: () => void;
}

export const CookieConsentModal: React.FC<CookieConsentModalProps> = ({
  onAccept,
  onDecline
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // Check if user has already given consent
    // ✅ SSR-Check
    if (typeof window === 'undefined' || typeof localStorage === 'undefined') return;
    
    const consent = localStorage.getItem('cookie_consent');
    if (!consent) {
      // Show modal after 1 second delay
      setTimeout(() => setIsVisible(true), 1000);
    }
  }, []);

  const handleAcceptAll = () => {
    // ✅ SSR-Check
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('cookie_consent', JSON.stringify({
        accepted: true,
        timestamp: new Date().toISOString(),
        functional: true,
        analytics: false
      }));
    }
    setIsVisible(false);
    if (onAccept) onAccept();
  };

  const handleAcceptNecessary = () => {
    // ✅ SSR-Check
    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('cookie_consent', JSON.stringify({
        accepted: true,
        timestamp: new Date().toISOString(),
        functional: false,
        analytics: false
      }));
    }
    setIsVisible(false);
    if (onDecline) onDecline();
  };

  const handleClose = () => {
    // User closed without choosing - treat as "necessary only"
    handleAcceptNecessary();
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
      <div className="glass-strong rounded-2xl max-w-2xl w-full shadow-2xl border border-white/10 animate-slide-up">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-500/20 rounded-xl">
              <Cookie className="w-6 h-6 text-orange-400" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Cookie-Einstellungen</h2>
              <p className="text-sm text-zinc-400 mt-1">
                Wir verwenden Cookies für eine bessere Nutzererfahrung
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-zinc-400 hover:text-white transition-colors p-1"
            aria-label="Schließen"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-zinc-300 mb-4">
            Complyo verwendet Cookies, um die Plattform sicher und funktionsfähig zu machen. 
            Sie können wählen, welche Cookie-Kategorien Sie akzeptieren möchten.
          </p>

          {/* Cookie Categories */}
          <div className="space-y-3 mb-6">
            {/* Notwendige Cookies */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-green-500/30">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                  <h3 className="font-semibold text-white">Notwendige Cookies</h3>
                </div>
                <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                  Immer aktiv
                </span>
              </div>
              <p className="text-sm text-zinc-400 mb-2">
                Diese Cookies sind für die Funktionsfähigkeit der Plattform erforderlich und können nicht deaktiviert werden.
              </p>
              {showDetails && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs text-zinc-500 pl-7">
                    • <strong>access_token:</strong> Authentifizierung (24h)
                  </div>
                  <div className="text-xs text-zinc-500 pl-7">
                    • <strong>refresh_token:</strong> Token-Erneuerung (7 Tage)
                  </div>
                  <div className="text-xs text-zinc-500 pl-7">
                    • <strong>session_id:</strong> Session-Management (Session)
                  </div>
                </div>
              )}
            </div>

            {/* Funktionale Cookies */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-purple-500/30">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Cookie className="w-5 h-5 text-purple-400 flex-shrink-0" />
                  <h3 className="font-semibold text-white">Funktionale Cookies</h3>
                </div>
                <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded">
                  Optional
                </span>
              </div>
              <p className="text-sm text-zinc-400 mb-2">
                Diese Cookies speichern Ihre Präferenzen (z.B. Theme, Sprache) für eine personalisierte Nutzererfahrung.
              </p>
              {showDetails && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs text-zinc-500 pl-7">
                    • <strong>user_preferences:</strong> UI-Einstellungen (unbegrenzt)
                  </div>
                  <div className="text-xs text-zinc-500 pl-7">
                    • <strong>cookie_consent:</strong> Cookie-Einwilligung (1 Jahr)
                  </div>
                </div>
              )}
            </div>

            {/* Analytics Cookies */}
            <div className="bg-zinc-800/50 rounded-lg p-4 border border-blue-500/30 opacity-50">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Shield className="w-5 h-5 text-blue-400 flex-shrink-0" />
                  <h3 className="font-semibold text-white">Analytics-Cookies</h3>
                </div>
                <span className="text-xs bg-zinc-700 text-zinc-400 px-2 py-1 rounded">
                  Nicht aktiv
                </span>
              </div>
              <p className="text-sm text-zinc-400">
                Aktuell werden keine Analytics-Cookies verwendet.
              </p>
            </div>
          </div>

          {/* Details Toggle */}
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-sm text-blue-400 hover:text-blue-300 transition-colors mb-4"
          >
            {showDetails ? '▼ Weniger Details' : '▶ Mehr Details anzeigen'}
          </button>

          {/* Datenschutz Link */}
          <p className="text-xs text-zinc-500 mb-4">
            Weitere Informationen finden Sie in unserer{' '}
            <a href="/privacy" target="_blank" className="text-blue-400 hover:text-blue-300 underline">
              Datenschutzerklärung
            </a>
            .
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 p-6 border-t border-white/10">
          <button
            onClick={handleAcceptNecessary}
            className="flex-1 px-6 py-3 bg-zinc-700 hover:bg-zinc-600 text-white rounded-lg font-semibold transition-colors"
          >
            Nur notwendige
          </button>
          <button
            onClick={handleAcceptAll}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-lg font-semibold shadow-lg hover:shadow-xl transition-all"
          >
            Alle akzeptieren
          </button>
        </div>
      </div>
    </div>
  );
};

export default CookieConsentModal;

