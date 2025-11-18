/** @type {import('next').NextConfig} */
const nextConfig = {
  // ✅ DEBUG MODE: Nicht minified, mit Source Maps
  productionBrowserSourceMaps: true,
  compiler: {
    removeConsole: false,
  },
  webpack: (config, { dev, isServer }) => {
    // ✅ Source Maps auch in Production
    config.devtool = 'source-map';
    
    // ✅ Nicht minifizieren
    if (!dev && !isServer) {
      config.optimization.minimize = false;
    }
    
    return config;
  },
  
  // Same as original config
  output: 'standalone',
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002'}/api/:path*`
      }
    ];
  },
  
  experimental: {
    serverActions: {
      bodySizeLimit: '2mb'
    }
  },
  
  images: {
    domains: ['api.complyo.tech', 'localhost'],
    unoptimized: true
  }
};

module.exports = nextConfig;

