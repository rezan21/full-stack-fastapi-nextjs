// Checks that a running production server caches only its landing page and static files, and keeps every other page out of shared caches.
import { argv, exit } from "node:process"

const base = argv[2] ?? "http://localhost:3000"
const problems: string[] = []
const nonces = new Set<string>()
let html = ""

const fetchPage = async (path: string) => {
  const response = await fetch(new URL(path, base), { redirect: "manual" })
  html += await response.clone().text()
  return {
    cache: response.headers.get("cache-control") ?? "",
    policy: response.headers.get("content-security-policy") ?? "",
    cookie: response.headers.get("set-cookie"),
  }
}

const landing = await fetchPage("/")
if (
  !/public[^,]*(,|$)/.test(landing.cache) ||
  !landing.cache.includes("s-maxage")
) {
  problems.push(
    `/: the landing page must be cacheable by a CDN, got "${landing.cache}"`,
  )
}
if (landing.cookie) problems.push("/: the landing page must not set a cookie")
if (/'nonce-/.test(landing.policy)) {
  problems.push("/: a cached page cannot carry a nonce")
}

const pages = ["/login", "/signup"]
for (const path of pages) {
  const { cache, policy } = await fetchPage(path)
  if (!cache.includes("no-store")) {
    problems.push(`${path}: a page must be no-store, got "${cache}"`)
  }
  const nonce = policy.match(/'nonce-([^']+)'/)?.[1]
  if (nonce) nonces.add(nonce)
  else problems.push(`${path}: the Content-Security-Policy has no nonce`)
}
if (nonces.size < pages.length)
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
  `ok: the landing page is cacheable, ${pages.length} pages are no-store with their own nonce, ${files.size} static files are immutable`,
)
