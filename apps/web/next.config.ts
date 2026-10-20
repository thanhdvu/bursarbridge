import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  // Gzip buffers the agent's SSE stream behind the /bbapi rewrite: progress steps then arrive all at once
  // with the reply (the "three dots for 15 seconds" wait). Serve uncompressed; put compression in front
  // of a production deploy only with SSE excluded.
  compress: false,
  async rewrites() {
    // Same-origin proxy to the FastAPI backend: no CORS, works on any port, streams SSE.
    const origin = process.env.BB_API_ORIGIN || "http://127.0.0.1:8000";
    return [{ source: "/bbapi/:path*", destination: `${origin}/api/:path*` }];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default withNextIntl(nextConfig);
