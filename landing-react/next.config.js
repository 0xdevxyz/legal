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
