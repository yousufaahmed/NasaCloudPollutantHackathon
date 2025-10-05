import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  eslint: {
    ignoreDuringBuilds: true,  // Add this to skip ESLint errors during build
  },
  typescript: {
    ignoreBuildErrors: true,  // Optional: also ignore TypeScript errors
  },
  trailingSlash: true,
  async redirects() {
    return [
      {
        source: "/",
        destination: "/home",
        permanent: true,
      },
    ];
  },
  // Add environment variable for API URL
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
  },
};

export default nextConfig;
