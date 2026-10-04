// Builds the Content-Security-Policy around the given script sources.
export function contentSecurityPolicy(scriptSources: string) {
  const dev = process.env.NODE_ENV === "development"
  return [
    "default-src 'self'",
    `script-src ${scriptSources}${dev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ].join("; ")
}
