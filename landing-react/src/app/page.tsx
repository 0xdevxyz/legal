import type { Metadata } from 'next';
import EarlyAccessLanding from '@/components/saas-landing/EarlyAccessLanding';
import WartelisteAbschnitt from '@/components/kampagne/WartelisteAbschnitt';

/**
 * Startseite: Hero, Website-Scanner, Preistabelle, darunter die Warteliste.
 *
 * Vom 02.09. bis zum Launch stand hier die Early-Access-Seite, weil Stripe auf
 * Testschluesseln lief und jeder Kaufversuch an einer echten Karte scheiterte.
 * Stripe ist seit 14.09.2026 live, elf Kaufwege legen Live-Sitzungen an, der
 * Webhook-Pfad ist seit 15.09. geprueft. Damit gehoert der Verkauf zurueck
 * auf "/".
 *
 * Was beim Zurueckdrehen mitgezogen wurde (test_startseite_indexierung.py
 * haelt es fest):
 * - robots index:true und canonical "/" bleiben HIER. /produkt behaelt
 *   noindex und zeigt kanonisch auf sich selbst; zwei indexierbare Seiten mit
 *   demselben Inhalt wuerden um dieselben Begriffe konkurrieren.
 * - Die Kampagnenkennung "startseite" bleibt, jetzt am Wartelisten-Abschnitt.
 *   /early-access traegt weiter "ea100-bfsg", sonst misst die Anzeige sich
 *   selbst.
 *
 * Die Kampagnenseite ist nicht geloescht: components/kampagne/
 * EarlyAccessKampagne.tsx liegt unveraendert unter /early-access.
 */
export const metadata: Metadata = {
  title: 'Complyo – Website-Compliance prüfen, reparieren, nachweisen',
  description:
    'BFSG, Cookies, Datenschutz und Rechtstexte in einem Scan. Befunde werden im Werkzeug behoben und im Browser nachgemessen. Scan kostenlos, Pro ab 89 € im Monat.',
  robots: { index: true, follow: true },
  alternates: { canonical: '/' },
  openGraph: {
    title: 'Complyo – Website-Compliance prüfen, reparieren, nachweisen',
    description:
      'Ein Scan für Barrierefreiheit, Cookies, Datenschutz und Rechtstexte. Befunde werden behoben und nachgemessen, mit Prüfprotokoll.',
    url: 'https://complyo.de',
    type: 'website',
  },
};

export default function Page() {
  // Eigene Kennung: organische Besucher der Startseite duerfen sich in der
  // Auswertung nicht mit dem bezahlten Anzeigen-Traffic von /early-access
  // vermischen.
  return (
    <EarlyAccessLanding>
      <WartelisteAbschnitt kampagne="startseite" />
    </EarlyAccessLanding>
  );
}
