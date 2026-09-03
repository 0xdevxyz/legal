import type { Metadata } from 'next';
import EarlyAccessLanding from '@/components/saas-landing/EarlyAccessLanding';

/**
 * Die bisherige Startseite: Hero, Website-Scanner und Preistabelle.
 *
 * Am 02.09.2026 von "/" hierher verschoben, nicht geloescht. Die Preistabelle
 * verlinkt auf app.complyo.de/register?plan=..., und mit Stripe im Testmodus
 * fuehrt jeder Bezahltarif in einen Checkout, der echte Karten ablehnt.
 * Deshalb ist die Seite vorerst nicht verlinkt und auf noindex — sie soll
 * ansehbar bleiben, aber keine Kaufversuche mehr einsammeln.
 *
 * Sobald Stripe auf Live-Schluessel steht, gehoert dieser Inhalt zurueck auf
 * "/" (siehe Kommentar in src/app/page.tsx).
 */
export const metadata: Metadata = {
  title: 'Complyo – Leistungsumfang und Preise',
  description:
    'Scan, KI-Reparatur und Prüfnachweis für DSGVO, TDDDG und Barrierefreiheit – Leistungsumfang und Tarife im Überblick.',
  // Kein Index, solange die Seite nicht die Startseite ist: sonst konkurriert
  // sie mit "/" um dieselben Begriffe und sammelt Klicks auf Kaufwege ein,
  // die derzeit nicht funktionieren.
  robots: { index: false, follow: true },
  alternates: { canonical: '/produkt/' },
};

export const dynamic = 'force-dynamic';

export default function Page() {
  return <EarlyAccessLanding />;
}
