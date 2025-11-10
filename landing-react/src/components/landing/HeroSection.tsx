'use client';

import React from 'react';
import { ArrowRight, PlayCircle, CheckCircle } from 'lucide-react';
import Image from 'next/image';

/**
 * HeroSection - Hauptbereich der Landing-Page
 * Inspiriert von Eye-Able® Design
 */
export default function HeroSection() {
  return (
    <section className="relative bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0" style={{
          backgroundImage: 'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
          backgroundSize: '40px 40px'
        }}></div>
      </div>
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left: Content */}
          <div className="text-center lg:text-left">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 bg-blue-500/20 border border-blue-400 rounded-full px-4 py-2 mb-6">
              <CheckCircle className="w-4 h-4 text-blue-400" />
              <span className="text-sm font-semibold text-blue-300">
                Über 2.500 Websites geschützt
              </span>
            </div>
            
            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
              Echte Compliance mit{' '}
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                KI-Unterstützung
              </span>
            </h1>
            
            {/* Subline */}
            <p className="text-xl text-gray-300 mb-8 leading-relaxed">
              Nachhaltige DSGVO-, Cookie- und Barrierefreiheit. 
              Keine Overlay-Lösungen – echte Code-Fixes für dauerhafte Compliance.
            </p>
            
            {/* USPs */}
            <div className="flex flex-col sm:flex-row gap-4 mb-8 text-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">Rechtssicher mit eRecht24</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">KI-generierte Lösungen</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                <span className="text-gray-300">WCAG 2.1 AA konform</span>
              </div>
            </div>
            
            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <a
                href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold px-8 py-4 rounded-xl transition-all shadow-lg hover:shadow-xl transform hover:scale-105"
              >
                Kostenlos starten
                <ArrowRight className="w-5 h-5" />
              </a>
              <a
                href="#demo"
                className="inline-flex items-center justify-center gap-2 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 text-white font-semibold px-8 py-4 rounded-xl transition-all"
              >
                <PlayCircle className="w-5 h-5" />
                Demo ansehen
              </a>
            </div>
            
            {/* Trust Indicators */}
            <div className="mt-12 pt-8 border-t border-white/10">
              <p className="text-sm text-gray-400 mb-4">Vertraut von führenden Unternehmen</p>
              <div className="flex items-center gap-8 flex-wrap justify-center lg:justify-start opacity-60">
                <div className="text-white font-bold text-lg">ACME Corp</div>
                <div className="text-white font-bold text-lg">TechStart</div>
                <div className="text-white font-bold text-lg">WebPro GmbH</div>
              </div>
            </div>
          </div>
          
          {/* Right: Hero Image / Dashboard Preview */}
          <div className="relative">
            {/* Glowing Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-500 blur-3xl opacity-20 rounded-3xl"></div>
            
            {/* Dashboard Screenshot Placeholder */}
            <div className="relative bg-gray-800 rounded-2xl shadow-2xl border border-gray-700 p-4">
              <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-xl p-6">
                {/* Mock Dashboard */}
                <div className="flex items-center justify-between mb-6">
                  <div className="text-sm text-gray-400">Compliance Score</div>
                  <div className="text-green-400 text-sm font-semibold">+47% Verbesserung</div>
                </div>
                
                {/* Circle Score */}
                <div className="flex items-center justify-center mb-8">
                  <div className="relative w-48 h-48">
                    <svg className="transform -rotate-90 w-48 h-48">
                      <circle
                        cx="96"
                        cy="96"
                        r="88"
                        stroke="#374151"
                        strokeWidth="12"
                        fill="none"
                      />
                      <circle
                        cx="96"
                        cy="96"
                        r="88"
                        stroke="url(#gradient)"
                        strokeWidth="12"
                        fill="none"
                        strokeDasharray={`${(92 / 100) * 553} 553`}
                        strokeLinecap="round"
                      />
                      <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#3B82F6" />
                          <stop offset="100%" stopColor="#8B5CF6" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-5xl font-bold text-white">92%</div>
                        <div className="text-sm text-gray-400">WCAG AA</div>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Mock Issues */}
                <div className="space-y-3">
                  <div className="flex items-center gap-3 bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-white">DSGVO-konform</div>
                      <div className="text-xs text-gray-400">Datenschutzerklärung vollständig</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-white">Barrierefreiheit</div>
                      <div className="text-xs text-gray-400">WCAG 2.1 Level AA erreicht</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                    <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                      <span className="text-white text-xs font-bold">3</span>
                    </div>
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-white">Quick Wins</div>
                      <div className="text-xs text-gray-400">In 15 Min umsetzbar</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Floating Badge */}
            <div className="absolute -bottom-4 -right-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white px-6 py-3 rounded-xl shadow-xl transform rotate-3">
              <div className="text-sm font-semibold">€50.000</div>
              <div className="text-xs opacity-90">Bußgeld vermieden</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Wave Divider */}
      <div className="absolute bottom-0 left-0 right-0">
        <svg viewBox="0 0 1440 120" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full">
          <path d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0V120Z" fill="#111827"/>
        </svg>
      </div>
    </section>
  );
}

