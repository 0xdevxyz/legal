/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Setzen des spezifischen Ports
  env: {
    PORT: '3002'
  }
}

module.exports = nextConfig
