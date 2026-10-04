---
paths:
  - "frontend/**/*"
---

# Next.js / React / Full-Stack Rules

## Next.js

- Be explicit about App Router vs Pages Router; never mix conventions.
- Server Components are the default; add `"use client"` only when interactivity/hooks/browser APIs are needed.
- Fetch data in Server Components or Route Handlers, not via client-side `useEffect`, unless polling or user-triggered refetch is required.
- Mutations use Server Actions where possible; use API routes only when a public API surface is needed.
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

- Reusable components are those in `components/common/` and `components/ui/`; feature components (`items/`, `settings/`, `auth/`, …) may call Server Actions and know their routes.
- Extract to a shared location only after use in two or more places, not on first write.
- Reusable components take data/callbacks as props; they don't fetch, mutate, or know about routes.
- No implicit coupling via shared mutable state between reusable components; use explicit props/context contracts.
- Control variants via a constrained prop (enum/`cva`-style), not open strings or scattered conditional classes.
- Never copy-paste a component with small tweaks; add a prop or composition slot instead.
- Form fields use `FormField` (`components/common/FormField.tsx`), not a hand-written `Controller`.

## Naming & Exports

- Directories under `frontend/src` are lowercase, and a component directory groups by feature (`components/items`), not by component.
- Component files are PascalCase and named after the component they export (`ItemsTable.tsx`). The shadcn-vendored `components/ui/` keeps the registry's kebab-case.
- Hook files in `hooks/` are kebab-case `use-*.ts`, matching the shadcn-generated `use-mobile.ts`; the exported function is camelCase (`useCustomToast`).
- Every other module (`lib/`, `actions/`, scripts, tests) is kebab-case.
- Named exports only. Default exports are for files Next.js or a tool requires (`app/` route files, `*.config.*`). Biome fails a stray default export or a file name that breaks these cases; directory casing is not machine-checked.

## Business Logic & Data

- Components render; business rules live in plain functions outside the component.
- Data access (fetch, SDK calls) lives in `lib/`, never inline in components. Server Actions live in `actions/` and stay thin: they call `lib/` through `authenticated()` or `attempt()` and revalidate, nothing more.
- Derived data is computed in a named function/hook, not inline via nested ternaries or chained `.filter().map()`.
- Components reach the server through Server Components (reads) and Server Actions (writes); custom hooks wrap browser-only APIs such as the clipboard, media queries and toasts.
- Every authenticated Server Action runs inside `authenticated()` and every public one inside `attempt()` (`lib/action-result.ts`), so the session guard and the error-to-result conversion are written once.
- Don't duplicate server-side validation on the client; share a schema (e.g. Zod) or defer to the server.
- More than one or two `useEffect` blocks per component signals logic that should move to a hook.

## Full-Stack

- Share types (or a schema) between client and server; never redeclare shapes that can drift. API calls, types and field constraints come from the generated SDK in `frontend/src/client/` (`bash scripts/generate-client.sh`), called through `lib/api.ts`; never hand-write URLs, API types or copies of backend constraints.
- Keep types strict; avoid `any`/`unknown`/loose dictionaries at API boundaries.
