'use client';

import React from 'react';
import { Check, Sparkles, Crown, ArrowRight, Shield, FileText, Eye, BarChart3 } from 'lucide-react';

const getAppUrl = (path: string) => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://localhost:3000${path}`;
    }
  }
  return `https://app.complyo.de${path}`;
};

/**
 * PricingTable - Flexibles 4-Säulen-Modell
 * Einzelne Säule: 19€/Monat
 * Alle 4 Säulen: 49€/Monat
 * Expertenservice: 2.990€ + 39€/Monat
 */
export default function PricingTable() {
  const pillars = [
    { name: 'Cookie & DSGVO', icon: Shield, color: 'blue' },
    { name: 'Barrierefreiheit', icon: Eye, color: 'purple' },
    { name: 'Rechtliche Texte', icon: FileText, color: 'green' },
    { name: 'Monitoring & Scan', icon: BarChart3, color: 'orange' },
  ];

  return (
    <section className="bg-gray-50 py-20" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Flexibles Pricing für Ihre Bedürfnisse
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Wählen Sie einzelne Module oder das komplette Paket - Sie entscheiden
          </p>
        </div>
        
        {/* Pricing Cards */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          
          {/* Einzelne Säule */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-gray-200 hover:border-blue-500 transition-all p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <Sparkles className="w-6 h-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-2xl font-bold text-gray-900">Einzelmodul</h3>
                <p className="text-sm text-gray-600">1 Säule nach Wahl</p>
              </div>
            </div>
            
            {/* Price */}
            <div className="mb-8">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold text-gray-900">19€</span>
                <span className="text-gray-600">/Monat</span>
              </div>
              <p className="text-sm text-gray-500 mt-2">zzgl. MwSt. pro Säule</p>
            </div>
            
            {/* Säulen Auswahl */}
            <div className="mb-6">
              <p className="font-semibold text-gray-700 mb-3">Wählen Sie eine Säule:</p>
              <div className="space-y-2">
                {pillars.map((pillar, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-gray-600 text-sm">
                    <pillar.icon className={`w-4 h-4 text-${pillar.color}-500`} />
                    <span>{pillar.name}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Features */}
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700 text-sm">Vollständige Funktionalität der gewählten Säule</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700 text-sm">KI-generierte Lösungen</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                <span className="text-gray-700 text-sm">E-Mail Support</span>
              </li>
            </ul>
            
            {/* CTA */}
            <a
              href={getAppUrl('/register?plan=single')}
              className="block w-full text-center bg-gray-100 hover:bg-gray-200 text-gray-900 font-semibold px-8 py-4 rounded-xl transition-all"
            >
              Modul wählen
            </a>
          </div>
          
          {/* Komplett-Paket */}
          <div className="bg-gradient-to-br from-blue-600 via-purple-600 to-blue-700 rounded-2xl shadow-2xl border-2 border-purple-400 relative p-8 text-white transform lg:scale-105">
            {/* Popular Badge */}
            <div className="absolute -top-4 left-1/2 -translate-x-1/2">
              <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-gray-900 font-bold px-6 py-2 rounded-full text-sm shadow-lg">
                ⭐ Beliebteste Wahl
              </div>
            </div>
            
            <div className="flex items-center gap-3 mb-6 mt-4">
              <div className="w-12 h-12 bg-white/20 backdrop-blur rounded-xl flex items-center justify-center">
                <Crown className="w-6 h-6 text-yellow-400" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">Komplett-Paket</h3>
                <p className="text-sm text-white/80">Alle 4 Säulen</p>
              </div>
            </div>
            
            {/* Price */}
            <div className="mb-8">
              <div className="flex items-baseline gap-2">
                <span className="text-5xl font-bold">49€</span>
                <span className="text-white/80">/Monat</span>
              </div>
              <p className="text-sm text-white/60 mt-2">zzgl. MwSt. • Sie sparen 27€/Monat</p>
            </div>
            
            {/* Alle 4 Säulen */}
            <div className="mb-6">
              <p className="font-semibold mb-3 text-yellow-400">Alle 4 Säulen inklusive:</p>
              <div className="grid grid-cols-2 gap-2">
                {pillars.map((pillar, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-white/90 text-sm">
                    <Check className="w-4 h-4 text-green-400" />
                    <span>{pillar.name}</span>
                  </div>
                ))}
              </div>
            </div>
            
            {/* Features */}
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-white/90 text-sm"><strong>Unbegrenzte</strong> Compliance-Analysen</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-white/90 text-sm"><strong>KI-generierte</strong> Code-Fixes</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-white/90 text-sm"><strong>KI-generierte</strong> Rechtstexte</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-white/90 text-sm"><strong>Priority</strong> Support</span>
              </li>
            </ul>
            
            {/* CTA */}
            <a
              href={getAppUrl('/register?plan=complete')}
              className="block w-full text-center bg-white hover:bg-gray-100 text-gray-900 font-bold px-8 py-4 rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
            >
              Jetzt starten
              <ArrowRight className="inline-block w-5 h-5 ml-2" />
            </a>
            
            <p className="text-center text-sm text-white/60 mt-4">
              Jederzeit kündbar
            </p>
          </div>
          
          {/* Expert Plan */}
          <div className="bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 rounded-2xl shadow-xl border-2 border-gray-700 p-8 text-white">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-orange-400 rounded-xl flex items-center justify-center">
                <Crown className="w-6 h-6 text-gray-900" />
              </div>
              <div>
                <h3 className="text-2xl font-bold">Expertenservice</h3>
                <p className="text-sm text-gray-400">Wir setzen alles um</p>
              </div>
            </div>
            
            {/* Price */}
            <div className="mb-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-3">
                <div className="text-sm text-gray-400 mb-1">Einmalig</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-4xl font-bold">2.990€</span>
                  <span className="text-gray-400">netto</span>
                </div>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                <div className="text-sm text-gray-400 mb-1">Danach laufend</div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-bold">39€</span>
                  <span className="text-gray-400">/Monat</span>
                </div>
              </div>
            </div>
            
            {/* Features */}
            <ul className="space-y-3 mb-8">
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm"><strong>Vollständige</strong> Umsetzung durch Experten</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm"><strong>WCAG 2.1 AA</strong> Zertifizierung</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm"><strong>Laufende Updates</strong> bei Gesetzesänderungen</span>
              </li>
              <li className="flex items-start gap-3">
                <Check className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <span className="text-gray-300 text-sm"><strong>Persönlicher</strong> Ansprechpartner</span>
              </li>
            </ul>
            
            {/* CTA */}
            <a
              href="/contact?service=expert"
              className="block w-full text-center bg-gradient-to-r from-yellow-400 to-orange-400 hover:from-yellow-500 hover:to-orange-500 text-gray-900 font-bold px-8 py-4 rounded-xl transition-all"
            >
              Beratung anfragen
            </a>
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

