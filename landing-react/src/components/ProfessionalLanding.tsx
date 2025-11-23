'use client';

import React from 'react';
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
export default function ProfessionalLanding() {
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
                  href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Login
                </a>
              </div>
            </div>
          </div>
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
      </footer>
    </div>
  );
}

