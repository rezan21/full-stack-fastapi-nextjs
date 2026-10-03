import path from "node:path"
import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  output: "standalone",
  outputFileTracingRoot: path.join(import.meta.dirname),
  allowedDevOrigins: ["frontend"],
  agentRules: false,
}

export default nextConfig
