/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  typescript: {
    ignoreBuildErrors: true, // TypeScript-Fehler während des Builds ignorieren
  },
  eslint: {
    ignoreDuringBuilds: true, // ESLint während des Builds ignorieren
  },
  
  env: {
    // Für lokale Entwicklung: http://localhost:8002
    // Für Production: https://api.complyo.tech (wird über .env gesetzt)
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002',
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/:path*`,
      },
    ];
  },
  
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
        ],
      },
    ];
  },
  
  images: {
    domains: ['complyo.tech', 'app.complyo.tech', 'api.complyo.tech'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
};

module.exports = nextConfig;
