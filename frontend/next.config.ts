import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // /api/* 轉發到 backend container
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://bebetter-backend:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
