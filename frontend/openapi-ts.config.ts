import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "../backend/openapi.json",
  output: "src/client",
  plugins: [
    "@hey-api/typescript",
    "@hey-api/sdk",
    "@hey-api/client-fetch",
    "zod",
  ],
})
