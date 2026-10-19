import type { Metadata } from 'next';
import EarlyAccessLanding from '@/components/saas-landing/EarlyAccessLanding';

/**
 * Die Produktseite: Hero, Website-Scanner und Preistabelle mit allen Tarifen.
 *
 * Am 02.09.2026 von "/" hierher verschoben, vom 28.09. bis 19.10. wieder auf
 * "/", seitdem erneut hier. Grund fuer den zweiten Umzug ist nicht mehr
 * Stripe (live seit 14.09.), sondern die Entscheidung, Inhabern vorn die
 * Warteliste zu zeigen und nur den Agentur-Tarif direkt zu verkaufen. Die
 * Seite bleibt erreichbar, aber unverlinkt und auf noindex, damit sie nicht
 * mit "/" um dieselben Begriffe konkurriert (siehe src/app/page.tsx und
 * test_startseite_indexierung.py).
 */
export const metadata: Metadata = {
  title: 'Complyo – Leistungsumfang und Preise',
  description:
    'Scan, KI-Reparatur und Prüfnachweis für DSGVO, TDDDG und Barrierefreiheit – Leistungsumfang und Tarife im Überblick.',
  // Kein Index, solange die Seite nicht die Startseite ist: sonst konkurriert
  // sie mit "/" um dieselben Begriffe.
  robots: { index: false, follow: true },
  alternates: { canonical: '/produkt/' },
};

export const dynamic = 'force-dynamic';

export default function Page() {
  return <EarlyAccessLanding />;
}
