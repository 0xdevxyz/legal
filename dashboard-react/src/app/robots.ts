import type { MetadataRoute } from 'next';

// app.complyo.de ist die eingeloggte Anwendung — nichts davon gehoert in
// eine Suchmaschine. Die oeffentlichen Marketing-Seiten liegen auf complyo.de.
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [{ userAgent: '*', disallow: '/' }],
  };
}
