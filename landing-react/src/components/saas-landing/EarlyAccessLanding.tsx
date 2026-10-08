'use client';
import React from 'react';
import HeroSection from './HeroSection';
import WebsiteScanner from '../landing/WebsiteScanner';
import PricingSection from './PricingSection';

/**
 * Die Produktseite: Hero, Scanner, Preistabelle.
 *
 * Der Name stammt aus der Zeit vor dem 02.09.2026 und ist geblieben, weil
 * /produkt und "/" ihn importieren. `children` stehen nach der Preistabelle
 * im selben <main>: die Startseite haengt dort die Warteliste an, /produkt
 * nichts.
 */
export default function EarlyAccessLanding({ children }: { children?: React.ReactNode }) {
  return (
    // Navigation und Fusszeile kommen aus dem Wurzel-Layout (Seitengeruest),
    // damit jede Seite dieselben Landmarks hat. Hier bleibt der Hauptinhalt.
    <main id="inhalt" tabIndex={-1} className="font-sans antialiased bg-white">
      <HeroSection />
      <WebsiteScanner />
      <PricingSection />
      {children}
    </main>
  );
}
