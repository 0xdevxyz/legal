'use client';

import React from 'react';
import { ArrowRight, Calendar } from 'lucide-react';

/**
 * CTASection - Finale Call-to-Action vor dem Footer
 */
export default function CTASection() {
  return (
    <section className="bg-gradient-to-br from-blue-600 via-purple-600 to-pink-600 text-white py-20">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          {/* Badge */}
          <div className="inline-block bg-white/20 backdrop-blur-sm border border-white/30 rounded-full px-6 py-2 mb-8">
            <span className="font-semibold">
              ⚡ Jetzt starten – keine Kreditkarte erforderlich
            </span>
          </div>
          
          {/* Headline */}
          <h2 className="text-4xl sm:text-5xl font-bold mb-6 leading-tight">
            Bereit für echte Compliance?
          </h2>
          
          {/* Subline */}
          <p className="text-xl text-white/90 mb-12 max-w-3xl mx-auto leading-relaxed">
            Schließen Sie sich über 2.500 Websites an, die mit Complyo rechtssicher und barrierefrei sind. 
            Starten Sie heute – Ihre erste Analyse ist kostenlos.
          </p>
          
          {/* CTAs */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <a
              href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
              className="inline-flex items-center justify-center gap-2 bg-white text-blue-600 hover:bg-gray-100 font-bold px-10 py-5 rounded-xl transition-all shadow-2xl hover:shadow-3xl transform hover:scale-105 text-lg"
            >
              Kostenlos starten
              <ArrowRight className="w-6 h-6" />
            </a>
            <a
              href="/contact?service=expert"
              className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 backdrop-blur-sm border-2 border-white text-white font-bold px-10 py-5 rounded-xl transition-all text-lg"
            >
              <Calendar className="w-6 h-6" />
              Beratung buchen
            </a>
          </div>
          
          {/* Trust Indicators */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-8 text-sm text-white/80">
            <div className="flex items-center gap-2">
              ✓ Keine Kreditkarte erforderlich
            </div>
            <div className="flex items-center gap-2">
              ✓ Jederzeit kündbar
            </div>
            <div className="flex items-center gap-2">
              ✓ DSGVO-konform
            </div>
          </div>
        </div>
        
        {/* Stats Row */}
        <div className="mt-16 pt-16 border-t border-white/20 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold mb-2">2.500+</div>
            <div className="text-white/80">Geschützte Websites</div>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2">€250k+</div>
            <div className="text-white/80">Vermiedene Bußgelder</div>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2">47%</div>
            <div className="text-white/80">Ø Score-Verbesserung</div>
          </div>
        </div>
      </div>
    </section>
  );
}

