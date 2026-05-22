import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // 仅在开发环境使用代理,生产环境使用NEXT_PUBLIC_API_URL
    if (process.env.NODE_ENV === 'development') {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:8000/api/:path*',
        },
      ];
    }
    return [];
  },
};

export default nextConfig;
