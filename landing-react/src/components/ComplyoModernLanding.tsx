'use client';

import React from 'react';
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
export default function ComplyoModernLanding() {
  return (
    <div className="min-h-screen bg-white overflow-hidden">
      {/* Header mit Hero Section */}
      <header>
        {/* Navigation */}
        <nav className="absolute top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-200" role="navigation" aria-label="Hauptnavigation">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center">
                <a href="/" className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent" aria-label="Zur Startseite">
                  Complyo
                </a>
              </div>
              <div className="hidden md:flex items-center space-x-8">
                <a href="#features" className="text-gray-700 hover:text-blue-600 transition-colors">Features</a>
                <a href="#pricing" className="text-gray-700 hover:text-blue-600 transition-colors">Preise</a>
                <a href="#faq" className="text-gray-700 hover:text-blue-600 transition-colors">FAQ</a>
                <a 
                  href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                  className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity"
                >
                  Login
                </a>
              </div>
            </div>
          </div>
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

