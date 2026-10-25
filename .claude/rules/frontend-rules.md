---
paths:
  - "frontend/**/*"
---

# Next.js / React / Full-Stack Rules

## Next.js

- Be explicit about App Router vs Pages Router; never mix conventions.
- Server Components are the default; add `"use client"` only when interactivity/hooks/browser APIs are needed.
- Fetch data in Server Components or Route Handlers, not via client-side `useEffect`, unless polling or user-triggered refetch is required.
- Mutations use Server Actions where possible. Use a Route Handler when the response has to be streamed (such as SSE) or when a public API surface is needed. Keep it thin: authenticate, validate with the generated schema, and forward through `lib/`. Next.js checks the `Origin` header for Server Actions only, so a Route Handler that acts on the session cookie checks it itself.
- Set caching/revalidation (`revalidate`, `dynamic`, fetch cache options) explicitly, don't rely on defaults.
- Validate all input in Route Handlers/Server Actions; never trust client-submitted data.
- Never import server-only env vars into client-bundled code; respect `NEXT_PUBLIC_` boundaries.

## React

- Functional components with hooks only, no class components.
- Co-locate state as close as possible to where it's used; avoid global state for local concerns.
- Prefer composition (children/slots) over context as a prop-drilling workaround.
- Memoise (`useMemo`, `useCallback`, `React.memo`) only for measured cost, not reflexively.
- `useEffect` is for syncing with external systems only, not for deriving state from props.

## Reusable Components

- Reusable components are the shared common and UI components; feature components (grouped by feature) may call Server Actions and know their routes.
- Extract to a shared location only after use in two or more places, not on first write.
- Reusable components take data/callbacks as props; they don't fetch, mutate, or know about routes.
- No implicit coupling via shared mutable state between reusable components; use explicit props/context contracts.
- Control variants via a constrained prop (enum/`cva`-style), not open strings or scattered conditional classes.
- Never copy-paste a component with small tweaks; add a prop or composition slot instead.
- Form fields use the shared form-field component, not a hand-written `Controller`.

## UI Primitives

- The shadcn style is `base-nova`, so UI primitives are Base UI (`@base-ui/react`). App code never imports Radix; Biome fails a `radix-ui` or `@radix-ui/*` import.
- Compose a component into a primitive with the `render` prop, never `asChild`; a pre-commit hook fails an `asChild` prop. `@assistant-ui/react` accepts both because it is built on Radix internally, and that stays inside the library.
- Add shadcn and assistant-ui registry components with the shadcn CLI, whose style-aware registry returns the Base UI flavor. Vendored registry code under `components/ui` and `components/assistant-ui` keeps what the registry ships and is outside Biome.

## Naming & Exports

- Directories are lowercase, and a component directory groups by feature, not by component.
- Component files are PascalCase and named after the component they export. Vendored registry components keep the registry's file names.
- Hook files are kebab-case `use-*.ts`; the exported function is camelCase.
- Every other module (`lib/`, `actions/`, scripts, tests) is kebab-case.
- Named exports only. Default exports are for files Next.js or a tool requires (`app/` route files, `*.config.*`). Biome fails a stray default export or a file name that breaks these cases; directory casing is not machine-checked.

## Business Logic & Data

- Components render; business rules live in plain functions outside the component.
- Data access (fetch, SDK calls) lives in `lib/`, never inline in components. Server Actions live in `actions/` and stay thin: they call `lib/` through the shared wrappers and revalidate, nothing more.
- Derived data is computed in a named function/hook, not inline via nested ternaries or chained `.filter().map()`.
- Components reach the server through Server Components (reads) and Server Actions (writes); custom hooks wrap browser-only APIs such as the clipboard, media queries and toasts.
- Every authenticated Server Action runs inside the shared session-guard wrapper and every public one inside the shared error-to-result wrapper, so both are written once.
- Don't duplicate server-side validation on the client; share a schema (e.g. Zod) or defer to the server.
- More than one or two `useEffect` blocks per component signals logic that should move to a hook.

## Full-Stack

- Share types (or a schema) between client and server; never redeclare shapes that can drift. API calls and types come from the generated SDK (regenerate it, never edit it), called through the shared API module; never hand-write URLs or API types. The one exception is a streamed response forwarded as it is: the generated SSE client parses every event and retries a POST, which a pass-through proxy must not do, so the API module calls the generated client in stream mode and a test ties its path to the spec.
- Keep types strict; avoid `any`/`unknown`/loose dictionaries at API boundaries.
