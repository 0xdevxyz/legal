import type { Metadata } from 'next';

/**
 * Das Impressum aus dem Suchindex nehmen.
 *
 * Auf /impressum stehen die Anbieterdaten einer natuerlichen Person: Name,
 * Wohnanschrift, Mobilnummer. Die Pflicht aus Paragraf 5 DDG ist, dass diese
 * Angaben auf der Website leicht erkennbar, unmittelbar erreichbar und
 * staendig verfuegbar sind. Sie in eine Suchmaschine zu stellen, verlangt
 * niemand. Das noindex aendert an der Erreichbarkeit fuer Besucher nichts.
 *
 * Wichtig: robots.txt bleibt auf 'Allow'. Ein Disallow verbietet Google das
 * ABRUFEN der Seite, der Crawler saehe das noindex dann nie, und eine bereits
 * indexierte URL bliebe im Index stehen. Genau das war im August 2026 bei
 * app.complyo.de/register und /login der Fall (siehe dashboard-react/src/app/
 * robots.ts). Crawlen erlauben, indexieren verbieten.
 *
 * Die Seite ist ausserdem aus src/app/sitemap.ts entfernt: eine Seite, die
 * nicht in den Index soll, gehoert nicht in die Sitemap.
 */
export const metadata: Metadata = {
  robots: {
    index: false,
    follow: true,
    googleBot: { index: false, follow: true },
  },
};

export default function ImpressumLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
