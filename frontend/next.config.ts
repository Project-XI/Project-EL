import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/docs',
        destination: '/docs.html',
      },
    ];
  },
};

export default nextConfig;
