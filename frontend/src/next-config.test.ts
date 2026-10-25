import { expect, test } from "bun:test"
import nextConfig from "../next.config"

test("shiki is bundled with the server code instead of loaded as an external package", () => {
  expect(nextConfig.transpilePackages).toContain("shiki")
})
