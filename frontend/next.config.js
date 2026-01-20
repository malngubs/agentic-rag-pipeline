/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better debugging
  reactStrictMode: true,
  
  // Image optimization configuration
  images: {
    domains: ['localhost', 'api.macrocomm.ai'],
    unoptimized: process.env.NODE_ENV === 'development',
  },
  
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8001',
  },
  
  // Webpack configuration
  webpack: (config, { isServer }) => {
    // Handle plotly.js
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
      };
    }
    
    return config;
  },
  
  // Headers for CORS and security
  async headers() {
    return [
      {
        source: '/:path*',
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
  
  // Redirects (none needed - /chat is the main page)
  async redirects() {
    return [];
  },
};

module.exports = nextConfig;
