'use client';

import React, { useState } from 'react';
import { Menu, X } from 'lucide-react';
import ModernHero from './modern-landing/ModernHero';
import TrustBanner from './modern-landing/TrustBanner';
import ProblemSection from './modern-landing/ProblemSection';
import FeaturesShowcase from './modern-landing/FeaturesShowcase';
import PricingModern from './modern-landing/PricingModern';
import IntegrationsSection from './modern-landing/IntegrationsSection';
import TestimonialsModern from './modern-landing/TestimonialsModern';
import ComplianceSection from './modern-landing/ComplianceSection';
import CTAModern from './modern-landing/CTAModern';
import FooterModern from './modern-landing/FooterModern';
import { Logo } from './Logo';

/**
 * ComplyoModernLanding - Hochprofessionelle Landing Page
 * Modernes, conversion-optimiertes Design
 * 
 * Features:
 * - Moderne Gradienten (Blau/Lila/Rosa)
 * - Glassmorphism-Effekte
 * - Smooth Animations mit Framer Motion
 * - Responsive Design
 * - Conversion-optimiert für technische Laien
 * 
 * ✅ Barrierefreiheit: Semantisches HTML5 (header, nav, main, footer)
 */
const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'https://app.complyo.tech';

export default function ComplyoModernLanding() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Header mit Hero Section */}
      <header>
        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200" role="navigation" aria-label="Hauptnavigation">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <a href="/" aria-label="Zur Startseite">
                  <Logo size="lg" variant="light" />
                </a>
              </div>
              <div className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-gray-700 hover:text-blue-600 transition-colors">Features</a>
                <a href="#pricing" className="text-gray-700 hover:text-blue-600 transition-colors">Preise</a>
                <a href="#faq" className="text-gray-700 hover:text-blue-600 transition-colors">FAQ</a>
                <a 
                  href={DASHBOARD_URL}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity"
                >
                  Login
                </a>
              </div>
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="md:hidden p-2 rounded-lg text-gray-700 hover:bg-gray-100 transition-colors"
                aria-label={mobileMenuOpen ? 'Menü schließen' : 'Menü öffnen'}
                aria-expanded={mobileMenuOpen}
              >
                {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
              </button>
            </div>
          </div>
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-gray-200 bg-white/95 backdrop-blur-md">
              <div className="px-4 py-4 space-y-3">
                <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-gray-700 hover:text-blue-600 font-medium py-2">Features</a>
                <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-gray-700 hover:text-blue-600 font-medium py-2">Preise</a>
                <a href="#faq" onClick={() => setMobileMenuOpen(false)} className="block text-gray-700 hover:text-blue-600 font-medium py-2">FAQ</a>
                <a href={DASHBOARD_URL} className="block bg-gradient-to-r from-blue-600 to-purple-600 text-white text-center px-4 py-3 rounded-lg hover:opacity-90 transition-opacity font-medium">Login</a>
              </div>
            </div>
          )}
        </nav>
        
        {/* Hero Section - Hauptbereich mit Statement */}
        <ModernHero />
      </header>
      
      {/* Hauptinhalt */}
      <main role="main">
        {/* Trust Banner - Logos und Vertrauen */}
        <TrustBanner />
        
        {/* Problem Section - Schmerzpunkte & Lösung */}
        <ProblemSection />
        
        {/* Features Showcase - Hauptfunktionen */}
        <FeaturesShowcase />
        
        {/* Compliance Section - Barrierefreiheit als Fokus */}
        <ComplianceSection />
        
        {/* Integrations - Issue Tracking etc. */}
        <IntegrationsSection />
        
        {/* Pricing - Modern und klar */}
        <PricingModern />
        
        {/* Testimonials - Kundenstimmen */}
        <TestimonialsModern />
        
        {/* Final CTA */}
        <CTAModern />
      </main>
      
      {/* Footer */}
      <footer role="contentinfo">
        <FooterModern />
      </footer>
    </div>
  );
}

