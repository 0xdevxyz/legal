import type { MetadataRoute } from 'next';

// app.complyo.de ist die eingeloggte Anwendung — nichts davon gehoert in
// eine Suchmaschine. Die oeffentlichen Marketing-Seiten liegen auf complyo.de.
//
// Warum hier trotzdem 'allow' steht (20.08.2026):
// Ein 'disallow: /' verbietet Google das ABRUFEN der Seiten. Damit sieht der
// Crawler das 'noindex, nofollow' aus dem Root-Layout nie — und eine bereits
// indexierte URL bleibt im Index stehen. Genau das war der Fall: register und
// login stehen seit dem 11.08. auf noindex und waren eine Woche spaeter
// unveraendert im Index.
//
// Crawlen muss also erlaubt sein, damit das noindex ueberhaupt greifen kann.
// Erst wenn die URLs aus dem Index verschwunden sind, waere ein erneutes
// Sperren per robots.txt sinnvoll — vorher haelt es sie dort fest.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: '*', allow: '/' }],
  };
}
