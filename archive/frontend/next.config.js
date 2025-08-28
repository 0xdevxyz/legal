/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://complyo-backend-healthy:8002/api/:path*'
      },
      {
        source: '/health',
        destination: 'http://complyo-backend-healthy:8002/health'
      },
      {
        source: '/api',
        destination: 'http://complyo-backend-healthy:8002/api'
      }
    ];
  },
  
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/json'
          },
          {
            key: 'Cache-Control', 
            value: 'no-store'
          }
        ]
      },
      {
        source: '/health',
        headers: [
          {
            key: 'Content-Type',
            value: 'application/json'
          }
        ]
      }
    ];
  },

  poweredByHeader: false
};

module.exports = nextConfig;
