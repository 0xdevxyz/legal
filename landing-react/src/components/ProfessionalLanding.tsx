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

/**
 * ProfessionalLanding - Professional Audit Dashboard Landing-Page
 * Inspiriert von Eye-Able® Design für maximale Glaubwürdigkeit
 */
export default function ProfessionalLanding() {
  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section with Dashboard Preview */}
      <HeroSection />
      
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
      
      {/* Final CTA */}
      <CTASection />
    </div>
  );
}

