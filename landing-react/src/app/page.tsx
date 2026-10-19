import type { Metadata } from 'next';
import EarlyAccessKampagne from '@/components/kampagne/EarlyAccessKampagne';

/**
 * Startseite: die Early-Access-Seite mit Warteliste, darunter der Agentur-
 * Tarif als Kaufweg.
 *
 * Verlauf: Vom 02.09. bis 28.09.2026 stand hier die Early-Access-Seite, weil
 * Stripe im Testmodus lief. Ab dem 28.09. verkaufte "/" wieder (Hero, Scanner,
 * Preistabelle, Warteliste darunter). Seit dem 19.10.2026 steht die Warteliste
 * wieder vorn: Inhaber einzelner Websites sichern sich den Early-Access-Preis
 * fuer Pro, Agenturen buchen ihren Tarif direkt (AgenturAbschnitt in
 * EarlyAccessKampagne). Die Preistabelle mit allen Tarifen bleibt unter
 * /produkt erreichbar, dort auf noindex.
 *
 * Was beim Tausch mitgezogen werden muss (test_startseite_indexierung.py
 * haelt es fest):
 * - robots index:true und canonical "/" bleiben HIER. Die Kampagnenseite
 *   /early-access traegt noindex und canonical auf sich selbst; wer sie
 *   unveraendert auf "/" legt, nimmt complyo.de aus dem Index.
 * - Die Kampagnenkennung "startseite" bleibt. /early-access traegt weiter
 *   "ea100-bfsg", sonst misst die Anzeige sich selbst.
 */
export const metadata: Metadata = {
  title: 'Complyo – Website-Compliance prüfen, reparieren, nachweisen',
  description:
    'BFSG, Cookies, Datenschutz und Rechtstexte in einem Scan. Befunde werden im Werkzeug behoben und im Browser nachgemessen. Early Access für die ersten 100, Agentur-Tarif sofort buchbar.',
  robots: { index: true, follow: true },
  alternates: { canonical: '/' },
  openGraph: {
    title: 'Complyo – Website-Compliance prüfen, reparieren, nachweisen',
    description:
      'Ein Scan für Barrierefreiheit, Cookies, Datenschutz und Rechtstexte. Befunde werden behoben und nachgemessen, mit Prüfprotokoll. Early Access für die ersten 100.',
    url: 'https://complyo.de',
    type: 'website',
  },
};

export default function Page() {
  // Eigene Kennung: organische Besucher der Startseite duerfen sich in der
  // Auswertung nicht mit dem bezahlten Anzeigen-Traffic von /early-access
  // vermischen.
  return <EarlyAccessKampagne kampagne="startseite" />;
}
