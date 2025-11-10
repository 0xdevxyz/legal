'use client';

import React from 'react';
import { Check, Sparkles, Crown, ArrowRight } from 'lucide-react';

/**
 * PricingTable - Preistabelle mit beiden Tarifen
 * DIY: 39€/Monat
 * Expertenservice: 2.900€ + 29€/Monat
 */
export default function PricingTable() {
  return (
    <section className="bg-gray-50 py-20" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Transparente Preise für echte Compliance
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Wählen Sie zwischen selbständiger Umsetzung oder Vollservice durch unsere Experten
          </p>
        </div>
        
        {/* Pricing Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* DIY Plan */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 hover:border-blue-500 transition-all p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">DIY mit KI</h3>
                <p className="text-sm text-gray-600">Für Selbermacher & Entwickler</p>
              </div>
            </div>
            
            {/* Price */}
            <div className="mb-8">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-gray-900">39€</span>
                <span className="text-gray-600">/Monat</span>
              </div>
              <p className="text-sm text-gray-500 mt-2">zzgl. MwSt.</p>
            </div>
            
            {/* Features */}
            <ul className="space-y-4 mb-8">
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>Unbegrenzte Compliance-Analysen</strong> für Ihre Websites
                </span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>KI-generierte Code-Fixes</strong> mit Copy-Paste Anleitungen
                </span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>Schritt-für-Schritt Erklärungen</strong> für jedes Problem
                </span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>Score-Verlauf & Reports</strong> zur Erfolgskontrolle
                </span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>PDF/Excel Export</strong> für Dokumentation
                </span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>eRecht24 Integration</strong> für rechtssichere Texte
                </span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700">
                  <strong>E-Mail Support</strong> bei Fragen
                </span>
              </li>
            </ul>
            
            {/* CTA */}
            <a
              href="/register?plan=diy"
              className="block w-full text-center bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold px-8 py-4 rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Jetzt starten
            </a>
            
            <p className="text-center text-sm text-gray-500 mt-4">
              Keine Vertragsbindung • Jederzeit kündbar
            </p>
          </div>
          
          {/* Expert Plan */}
          <div className="bg-gradient-to-br from-gray-900 via-purple-900 to-blue-900 rounded-2xl shadow-2xl border-2 border-purple-500 relative p-8 text-white transform lg:scale-105">
            {/* Popular Badge */}
            <div className="absolute -top-4 left-1/2 -translate-x-1/2">
              <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-gray-900 font-bold px-6 py-2 rounded-full text-sm shadow-lg">
                ⭐ Empfohlen
              </div>
            </div>
            
            <div className="flex items-center gap-3 mb-6 mt-4">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-400 rounded-xl flex items-center justify-center">
                <Crown className="w-6 h-6 text-gray-900" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">Expertenservice</h3>
                <p className="text-sm text-gray-300">Vollständige Umsetzung für Sie</p>
              </div>
            </div>
            
            {/* Price */}
            <div className="mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-3">
                <div className="text-sm text-gray-300 mb-1">Einmalig</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">2.900€</span>
                  <span className="text-gray-300">netto</span>
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-sm text-gray-300 mb-1">Danach laufend</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold">29€</span>
                  <span className="text-gray-300">/Monat</span>
                </div>
              </div>
            </div>
            
            {/* Einmalige Leistungen */}
            <div className="mb-6">
              <h4 className="font-semibold mb-3 text-yellow-400">Einmalige Umsetzung (2.900€):</h4>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Vollständige Website-Analyse</strong> durch Experten
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Professionelle Code-Umsetzung</strong> aller Compliance-Anforderungen
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>WCAG 2.1 AA Zertifizierung</strong> der Barrierefreiheit
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>eRecht24 Integration</strong> mit rechtssicheren Texten
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Cookie-Consent Implementation</strong> DSGVO-konform
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Barrierefreiheit-Optimierung</strong> des gesamten Codes
                  </span>
                </li>
              </ul>
            </div>
            
            {/* Laufende Leistungen */}
            <div className="mb-8">
              <h4 className="font-semibold mb-3 text-blue-400">Laufende Updates (29€/Monat):</h4>
              <ul className="space-y-3">
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Monatliche Compliance-Updates</strong> bei Gesetzesänderungen
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Automatische Anpassungen</strong> für neue Rechtslage
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Priority Support</strong> per E-Mail & Telefon
                  </span>
                </li>
                <li className="flex items-start gap-3">
                  <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                  <span className="text-gray-100">
                    <strong>Monitoring & Alerts</strong> bei Compliance-Risiken
                  </span>
                </li>
              </ul>
            </div>
            
            {/* CTA */}
            <a
              href="/contact?service=expert"
              className="block w-full text-center bg-gradient-to-r from-yellow-400 to-orange-400 hover:from-yellow-500 hover:to-orange-500 text-gray-900 font-bold px-8 py-4 rounded-xl transition-all shadow-lg hover:shadow-2xl transform hover:scale-105 mb-3"
            >
              Beratung vereinbaren
              <ArrowRight className="inline-block w-5 h-5 ml-2" />
            </a>
            
            <p className="text-center text-sm text-gray-300">
              Für Unternehmen ohne technisches Know-how
            </p>
          </div>
        </div>
        
        {/* Trust Message */}
        <div className="text-center mt-12">
          <p className="text-gray-600">
            💳 Sichere Zahlung • 🔒 DSGVO-konform • 📄 Transparente Rechnung
          </p>
        </div>
      </div>
    </section>
  );
}

