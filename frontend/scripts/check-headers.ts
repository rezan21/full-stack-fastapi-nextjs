// Checks that a running production server keeps pages out of shared caches and serves its static files immutable.
import { argv, exit } from "node:process"

const base = argv[2] ?? "http://localhost:3000"
const problems: string[] = []
const nonces = new Set<string>()
let html = ""

const paths = ["/", "/login", "/signup"]
for (const path of paths) {
  const response = await fetch(new URL(path, base), { redirect: "manual" })
  const cache = response.headers.get("cache-control") ?? ""
  if (!cache.includes("no-store")) {
    problems.push(`${path}: a page must be no-store, got "${cache}"`)
  }
  const policy = response.headers.get("content-security-policy") ?? ""
  const nonce = policy.match(/'nonce-([^']+)'/)?.[1]
  if (nonce) nonces.add(nonce)
  else problems.push(`${path}: the Content-Security-Policy has no nonce`)
  html += await response.text()
}
if (nonces.size < paths.length)
  problems.push("the nonce must differ on every response")

const files = new Set(
  html.match(/\/_next\/static\/[^"')\s]+\.(?:js|css|svg|png)/g),
)
if (files.size === 0) problems.push("found no static files in the pages")
for (const file of files) {
  const cache =
    (await fetch(new URL(file, base))).headers.get("cache-control") ?? ""
  if (!cache.includes("immutable")) {
    problems.push(`${file}: a static file must be immutable, got "${cache}"`)
  }
}

if (problems.length > 0) {
  console.error(problems.join("\n"))
  exit(1)
}
console.log(
  `ok: ${paths.length} pages are no-store with their own nonce, ${files.size} static files are immutable`,
)
