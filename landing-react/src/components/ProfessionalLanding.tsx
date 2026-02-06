'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import HeroSection from './landing/HeroSection';
import WebsiteScanner from './landing/WebsiteScanner';
import VideoDemo from './landing/VideoDemo';
import ProductFeatures from './landing/ProductFeatures';
import InteractiveDemo from './landing/InteractiveDemo';
import BenefitsGrid from './landing/BenefitsGrid';
import ComplianceBadges from './landing/ComplianceBadges';
import Testimonials from './landing/Testimonials';
import PricingTable from './landing/PricingTable';
import FAQAccordion from './landing/FAQAccordion';
import TrustMetrics from './landing/TrustMetrics';
import CTASection from './landing/CTASection';
import { Logo } from './Logo';

/**
 * ProfessionalLanding - Professional Audit Dashboard Landing-Page
 * Inspiriert von Eye-Able® Design für maximale Glaubwürdigkeit
 * 
 * ✅ Barrierefreiheit: Semantisches HTML5 (header, nav, main, footer)
 */
const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'https://app.complyo.tech';

export default function ProfessionalLanding() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-white">
      {/* Header mit Hero Section */}
      <header>
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200" role="navigation" aria-label="Hauptnavigation">
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
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
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
            <div className="md:hidden border-t border-gray-200 bg-white">
              <div className="px-4 py-4 space-y-3">
                <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-gray-700 hover:text-blue-600 font-medium py-2">Features</a>
                <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-gray-700 hover:text-blue-600 font-medium py-2">Preise</a>
                <a href="#faq" onClick={() => setMobileMenuOpen(false)} className="block text-gray-700 hover:text-blue-600 font-medium py-2">FAQ</a>
                <a href={DASHBOARD_URL} className="block bg-blue-600 text-white text-center px-4 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium">Login</a>
              </div>
            </div>
          )}
        </nav>
        
        {/* Hero Section with Dashboard Preview */}
        <HeroSection />
      </header>
      
      {/* Hauptinhalt */}
      <main role="main">
        {/* Website Scanner - Hauptfeature */}
        <WebsiteScanner />
        
        {/* Video Demo showing Workflow */}
        <VideoDemo />
        
        {/* Trust Metrics */}
        <TrustMetrics />
        
        {/* Product Features with Screenshots */}
        <ProductFeatures />
        
        {/* Interactive Demos */}
        <InteractiveDemo />
        
        {/* Benefits Grid */}
        <BenefitsGrid />
        
        {/* Compliance Badges */}
        <ComplianceBadges />
        
        {/* Testimonials Slider */}
        <Testimonials />
        
        {/* Pricing Table */}
        <PricingTable />
        
        {/* FAQ Accordion */}
        <FAQAccordion />
      </main>
      
      {/* Footer mit Final CTA */}
      <footer role="contentinfo">
        <CTASection />
        <div className="bg-gray-900 text-gray-400 py-8">
          <div className="max-w-7xl mx-auto flex flex-col items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 md:flex-row">
            <p className="text-sm">&copy; {new Date().getFullYear()} Complyo GmbH. Alle Rechte vorbehalten.</p>
            <div className="flex items-center gap-6 text-sm">
              <Link href="/impressum" className="hover:text-white transition">Impressum</Link>
              <Link href="/datenschutz" className="hover:text-white transition">Datenschutz</Link>
              <Link href="/agb" className="hover:text-white transition">AGB</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

