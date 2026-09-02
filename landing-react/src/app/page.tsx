import type { Metadata } from 'next';
import EarlyAccessKampagne from '@/components/kampagne/EarlyAccessKampagne';

/**
 * Startseite.
 *
 * Seit 02.09.2026 steht hier die Early-Access-Seite statt der Produktseite mit
 * Preistabelle. Grund: Stripe laeuft auf Testschluesseln (sk_test_/pk_test_),
 * jeder Klick auf "Pro buchen" landete in einem Checkout, in dem echte Karten
 * abgelehnt werden. Eine Warteliste ist die ehrliche Ansage, solange nicht
 * kassiert werden kann.
 *
 * Die alte Startseite ist NICHT geloescht: sie liegt unveraendert in
 * components/saas-landing/EarlyAccessLanding.tsx und ist unter /produkt
 * erreichbar. Zurueckdrehen heisst, hier wieder EarlyAccessLanding zu
 * rendern und die Metadaten aus /produkt hierher zu holen.
 *
 * Anders als /early-access ist diese Seite indexierbar. Ein noindex auf "/"
 * wuerde complyo.de aus der Suche nehmen — der Preisvorteil steht damit
 * oeffentlich, das ist die bewusste Folge der Entscheidung.
 */
export const metadata: Metadata = {
  title: 'Complyo – Website-Compliance prüfen, reparieren, nachweisen',
  description:
    'BFSG, Cookies, Datenschutz und Rechtstexte in einem Scan. Befunde werden behoben und im Browser nachgemessen. Jetzt für den Early Access vormerken lassen.',
  robots: { index: true, follow: true },
  alternates: { canonical: '/' },
  openGraph: {
    title: 'Complyo – Website-Compliance prüfen, reparieren, nachweisen',
    description:
      'Ein Scan für Barrierefreiheit, Cookies, Datenschutz und Rechtstexte. Befunde werden behoben und nachgemessen. Early Access für die ersten 100.',
    url: 'https://complyo.de',
    type: 'website',
  },
};

export default function Page() {
  // Eigene Kennung: organische Besucher der Startseite duerfen sich in der
  // Auswertung nicht mit dem bezahlten Anzeigen-Traffic von /early-access
  // vermischen, sonst misst die Kampagne sich selbst.
  return <EarlyAccessKampagne kampagne="startseite" />;
}
