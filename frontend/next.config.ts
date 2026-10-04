import path from "node:path"
import type { NextConfig } from "next"
import { contentSecurityPolicy } from "./src/lib/csp"

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  {
    key: "Permissions-Policy",
    value: "camera=(), microphone=(), geolocation=()",
  },
]

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname),
  allowedDevOrigins: ["frontend"],
  agentRules: false,
  poweredByHeader: false,
  headers: async () => [
    { source: "/(.*)", headers: securityHeaders },
    {
      source: "/",
      headers: [
        {
          key: "Content-Security-Policy",
          value: contentSecurityPolicy("'self' 'unsafe-inline'"),
        },
        { key: "Cache-Control", value: "public, max-age=0, s-maxage=300" },
      ],
    },
  ],
}

export default nextConfig
