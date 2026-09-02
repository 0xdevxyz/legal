import type { Metadata } from 'next';
import EarlyAccessKampagne from '@/components/kampagne/EarlyAccessKampagne';

export const metadata: Metadata = {
  title: 'Complyo Early Access: die ersten 100 zahlen 35 € statt 49 €',
  description:
    'BFSG, Cookies, Datenschutz und Rechtstexte in einem Scan – Befunde werden behoben und nachgemessen. Trag dich ein und sichere dir 35 € statt 49 € im Monat, das erste Jahr.',
  // Bewusst nicht indexieren. Die Seite traegt ein befristetes Sonderangebot;
  // steht es dauerhaft in der Suche, untergraebt es den regulaeren Preis auf
  // der Startseite und bleibt sichtbar, wenn die 100 Plaetze laengst weg sind.
  // Fuer bezahlten Traffic ist Indexierung ohnehin nicht noetig.
  robots: { index: false, follow: true },
  alternates: { canonical: '/early-access/' },
  openGraph: {
    title: 'Complyo Early Access: die ersten 100 zahlen 35 € statt 49 €',
    description:
      'Website auf BFSG, Cookies, Datenschutz und Rechtstexte prüfen, Befunde beheben, Ergebnis nachmessen. Early-Access-Preis für die ersten 100.',
    url: 'https://complyo.de/early-access',
    type: 'website',
  },
};

export default function Page() {
  return <EarlyAccessKampagne />;
}
