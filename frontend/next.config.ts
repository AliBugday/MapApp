import type { NextConfig } from "next";

// Reaching Django over the compose network. The browser never uses this URL.
const backendUrl = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";

const nextConfig: NextConfig = {
  // Report photos are served from Django's /media/ proxy, already same-origin and already
  // cheap (thumbnails are pre-generated server-side) — the optimizer would only add a
  // round trip through the proxy for no benefit.
  images: { unoptimized: true },

  // Django/DRF requires a trailing slash on every URL-conf route; Next's default
  // trailing-slash redirect would strip it before the rewrite below ever runs, and
  // even with that redirect disabled, the :path* wildcard drops a trailing slash when
  // it re-interpolates the destination. Both are worked around below.
  skipTrailingSlashRedirect: true,

  // Everything below is proxied so the browser only ever talks to localhost:3000.
  // Same origin means no CORS, and Django's session cookie is set on this origin,
  // so logging in through /admin also authenticates requests made from the map.
  async rewrites() {
    return [
      // Force the trailing slash back on for Django's URL-conf routes — :path* strips it.
      { source: "/api/:path*", destination: `${backendUrl}/api/:path*/` },
      { source: "/admin/:path*", destination: `${backendUrl}/admin/:path*/` },
      { source: "/api-auth/:path*", destination: `${backendUrl}/api-auth/:path*/` },
      // Static/media are literal file paths, never slash-terminated — left as-is.
      { source: "/static/:path*", destination: `${backendUrl}/static/:path*` },
      { source: "/media/:path*", destination: `${backendUrl}/media/:path*` },
    ];
  },
};

export default nextConfig;
