/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // ✅ FÜR PRODUCTION DOCKER BUILD ERFORDERLICH
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.de',
  },
  
  trailingSlash: true,
  
  // Sicherheitskopfzeilen setzt ausschliesslich nginx
  // (/etc/nginx/sites-available/complyo.de, Kopie in nginx/complyo.de).
  // Hier standen sie ein zweites Mal, mit zwei Widerspruechen: X-Frame-Options
  // DENY gegen SAMEORIGIN und Referrer-Policy origin-when-cross-origin gegen
  // strict-origin-when-cross-origin. Bei zwei CSP-Kopfzeilen wendet der Browser
  // den Schnitt an, es galt also eine Regel, die in keiner der beiden Dateien
  // vollstaendig stand.
  //
  // nginx ist die richtige Stelle, weil es mehr ausliefert als diese App:
  // /nachweis/<site>/<token> geht direkt an das Backend auf Port 8002. Eine CSP
  // von hier erreicht diese Seiten nie.
  //
  // Folge fuer die Entwicklung: unter `next dev` kommt keine dieser Kopfzeilen,
  // gemessen wird deshalb immer live hinter nginx.
  
  images: {
    domains: ['complyo.de', 'api.complyo.de'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: 'https://app.complyo.de',
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
