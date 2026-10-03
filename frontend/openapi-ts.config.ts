import { defineConfig } from "@hey-api/openapi-ts"

export default defineConfig({
  input: "../backend/openapi.json",
  output: "src/client",
  plugins: [
    "@hey-api/typescript",
    { name: "@hey-api/sdk", validator: { request: "zod", response: false } },
    "@hey-api/client-fetch",
    { name: "zod", responses: false },
  ],
})
