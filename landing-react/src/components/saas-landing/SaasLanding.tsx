'use client';
import React from 'react';
import NavBar from './NavBar';
import HeroSection from './HeroSection';
import ExploreSection from './ExploreSection';
import FeaturesSection from './FeaturesSection';
import AnalyticsSection from './AnalyticsSection';
import PricingSection from './PricingSection';
import IntegrationsSection from './IntegrationsSection';
import TestimonialsSection from './TestimonialsSection';
import CTABanner from './CTABanner';
import FAQSection from './FAQSection';
import FooterSection from './FooterSection';
import WebsiteScanner from '../landing/WebsiteScanner';

export default function SaasLanding() {
  return (
    <main className="font-sans antialiased bg-white">
      <NavBar />
      <HeroSection />
      <WebsiteScanner />
      <ExploreSection />
      <FeaturesSection />
      <AnalyticsSection />
      <PricingSection />
      <IntegrationsSection />
      <TestimonialsSection />
      <CTABanner />
      <FAQSection />
      <FooterSection />
    </main>
  );
}
