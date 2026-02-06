'use client';

import React, { useState } from 'react';
import { X, Check, Zap, CreditCard, Lock } from 'lucide-react';
import { createStripeCheckout } from '@/lib/api';

interface PaywallModalProps {
  isOpen: boolean;
  onClose: () => void;
  domain?: string;
  fixesUsed?: number;
  fixesLimit?: number;
}

export const StripePaywallModal: React.FC<PaywallModalProps> = ({ 
  isOpen, 
  onClose,
  domain,
  fixesUsed = 1,
  fixesLimit = 1
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpgrade = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Erstelle Stripe Checkout Session via API (mit Domain!)
      const response = await createStripeCheckout('pro', 'monthly', domain);

      // Zeige Dev-Mode Hinweis falls aktiviert
      if (response.dev_mode) {
        console.warn('⚠️ ENTWICKLUNGSMODUS: Zahlung wurde simuliert');
        // Optional: Toast-Benachrichtigung anzeigen
        alert('⚠️ Entwicklungsmodus: Zahlung wurde simuliert. Sie werden direkt weitergeleitet.');
      }

      // Redirect zu Stripe Checkout (oder im Dev-Mode direkt zur Success-Seite)
      window.location.href = response.checkout_url;
    } catch (err: any) {
      console.error('Upgrade failed:', err);
      setError(err.message || 'Ein Fehler ist aufgetreten');
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-2xl max-w-md w-full border-2 border-yellow-500/50 shadow-2xl relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
          aria-label="Schließen"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Header */}
        <div className="text-center p-8 pb-6">
          <div className="text-5xl mb-4 animate-bounce">🎉</div>
          <h2 className="text-2xl font-bold text-white mb-2">
            Ihr kostenloser Fix wurde genutzt!
          </h2>
          <p className="text-gray-400">
            Upgraden Sie jetzt für unbegrenzte Fixes an dieser Domain
          </p>
          {domain && (
            <div className="mt-3 inline-block bg-blue-500/20 border border-blue-500 rounded-lg px-3 py-1 text-blue-300 text-sm font-semibold">
              🌐 {domain}
            </div>
          )}
          <div className="mt-4 text-sm text-gray-500">
            {fixesUsed} von {fixesLimit} Fixes verwendet
          </div>
        </div>

        {/* Pricing Card */}
        <div className="px-8 pb-6">
          <div className="bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl p-6 mb-6">
            <div className="text-center text-white mb-4">
              <div className="text-4xl font-bold mb-1">49€</div>
              <div className="text-sm opacity-90">pro Monat • Alle 4 Säulen</div>
            </div>

            <ul className="space-y-3 text-white text-sm">
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span><strong>Unbegrenzte KI-Fixes</strong> für diese Domain</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span><strong>Schritt-für-Schritt Anleitungen</strong> mit Copy-Paste Code</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span><strong>Score-Verlauf & Reports</strong> zur Erfolgskontrolle</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span><strong>eRecht24 Integration</strong> für rechtssichere Texte</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span><strong>PDF/Excel Export</strong> für Dokumentation</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span><strong>E-Mail Support</strong> bei Fragen</span>
              </li>
            </ul>
          </div>

          {/* Info Box - Domain Lock */}
          <div className="mb-4 p-3 bg-blue-500/20 border border-blue-500 rounded-lg text-blue-300 text-xs">
            ℹ️ <strong>Hinweis:</strong> Dieses Abo gilt nur für die aktuell analysierte Domain. 
            Einzelne Säulen ab 19€/Monat oder alle 4 Säulen für 49€/Monat.
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg text-red-300 text-sm">
              {error}
            </div>
          )}

          {/* CTA Button */}
          <button
            onClick={handleUpgrade}
            disabled={loading}
            className="w-full bg-yellow-500 hover:bg-yellow-600 disabled:bg-gray-700 disabled:cursor-not-allowed text-gray-900 font-bold py-4 rounded-xl transition-all mb-3 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
                Wird geladen...
              </>
            ) : (
              <>
                <Zap className="w-5 h-5" />
                Jetzt upgraden
              </>
            )}
          </button>

          {/* Trust Badges */}
          <div className="flex items-center justify-center gap-4 text-xs text-gray-500 mb-3">
            <div className="flex items-center gap-1">
              <Lock className="w-3 h-3" />
              <span>Sichere Zahlung</span>
            </div>
            <div className="flex items-center gap-1">
              <CreditCard className="w-3 h-3" />
              <span>Stripe</span>
            </div>
          </div>

          {/* Later Button */}
          <button
            onClick={onClose}
            disabled={loading}
            className="w-full text-gray-400 hover:text-white text-sm py-2 transition-colors"
          >
            Später
          </button>
        </div>
      </div>
    </div>
  );
};

