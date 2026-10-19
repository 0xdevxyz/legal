'use client';
import React from 'react';
import HeroSection from './HeroSection';
import WebsiteScanner from '../landing/WebsiteScanner';
import PricingSection from './PricingSection';

/**
 * Die Produktseite: Hero, Scanner, Preistabelle.
 *
 * Der Name stammt aus der Zeit vor dem 02.09.2026. Seit dem 19.10.2026
 * importiert nur noch /produkt die Komponente; "/" zeigt die
 * EarlyAccessKampagne. `children` stehen nach der Preistabelle im selben
 * <main> (vom 28.09. bis 19.10. hing die Startseite dort die Warteliste an,
 * WartelisteAbschnitt liegt dafuer weiter in components/kampagne/).
 */
export default function EarlyAccessLanding({ children }: { children?: React.ReactNode }) {
  return (
    // Navigation und Fusszeile kommen aus dem Wurzel-Layout (Seitengeruest),
    // damit jede Seite dieselben Landmarks hat. Hier bleibt der Hauptinhalt.
    <main id="inhalt" tabIndex={-1} className="font-sans antialiased bg-nacht-950">
      <HeroSection />
      <WebsiteScanner />
      <PricingSection />
      {children}
    </main>
  );
}
