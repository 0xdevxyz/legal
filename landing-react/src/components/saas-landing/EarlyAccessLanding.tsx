'use client';
import React from 'react';
import HeroSection from './HeroSection';
import WebsiteScanner from '../landing/WebsiteScanner';
import PricingSection from './PricingSection';

export default function EarlyAccessLanding() {
  return (
    // Navigation und Fusszeile kommen aus dem Wurzel-Layout (Seitengeruest),
    // damit jede Seite dieselben Landmarks hat. Hier bleibt der Hauptinhalt.
    <main id="inhalt" tabIndex={-1} className="font-sans antialiased bg-white">
      <HeroSection />
      <WebsiteScanner />
      <PricingSection />
    </main>
  );
}
