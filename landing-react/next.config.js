/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // ✅ FÜR PRODUCTION DOCKER BUILD ERFORDERLICH
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech',
  },
  
  trailingSlash: true,
  
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
          {
            // 'unsafe-inline' wegen Next.js-Hydration & Tailwind (keine Nonce-Middleware).
            // Widgets (Cookie/Accessibility) von api.complyo.de; Cookie-Widget zieht
            // Google-Fonts-CSS; YouTube-Embed im Video-Demo. Spiegelt nginx (complyo.de).
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-inline' https://api.complyo.de",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://api.complyo.de",
              "font-src 'self' data: https://fonts.gstatic.com",
              "img-src 'self' data: blob: https://cdn.complyo.tech https://api.complyo.de https://i.ytimg.com",
              "connect-src 'self' https://api.complyo.de https://app.complyo.de https://cdn.complyo.tech",
              "frame-src https://www.youtube.com https://www.youtube-nocookie.com",
              "frame-ancestors 'self'",
              "base-uri 'self'",
              "form-action 'self' https://app.complyo.de",
              "object-src 'none'",
              "upgrade-insecure-requests",
            ].join('; '),
          },
        ],
      },
    ];
  },
  
  images: {
    domains: ['complyo.tech', 'api.complyo.tech'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: 'https://app.complyo.tech',
        permanent: true,
      },
    ];
  },
};

module.exports = nextConfig;
