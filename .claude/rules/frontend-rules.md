---
paths:
  - "frontend/**/*"
  - "**/*.{ts,tsx,js,jsx,css}"
---

# Next.js / React / Full-Stack Rules

## Agent Behaviour

- State assumptions before acting; do not silently guess on ambiguous requirements.
- Minimise scope: touch only files the task requires, no drive-by refactors.
- Deletion is valid: remove code the change makes obsolete, don't leave it "for safety."
- No speculative abstraction; solve the problem in front of you, not a hypothetical future one.
- Verify claims: run test/build/lint before saying something works.
- Comments explain "why," never restate "what" the code already shows.

## Next.js

- Read the framework docs (`node_modules/next/dist/docs/` or official docs) before writing Next.js-specific code; training data may be outdated.
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

- Extract to a shared location only after use in two or more places, not on first write.
- Components take data/callbacks as props; they don't fetch, mutate, or know about routes.
- No implicit coupling via shared mutable state between reusable components; use explicit props/context contracts.
- Control variants via a constrained prop (enum/`cva`-style), not open strings or scattered conditional classes.
- Never copy-paste a component with small tweaks; add a prop or composition slot instead.

## Business Logic & Data

- Components render; business rules live in plain functions outside the component.
- Data access (fetch, DB queries, Server Action bodies) lives in `lib/`/`services/`, never inline in components.
- Derived data is computed in a named function/hook, not inline via nested ternaries or chained `.filter().map()`.
- Custom hooks are the boundary between components and the outside world (API clients, stores).
- Don't duplicate server-side validation on the client; share a schema (e.g. Zod) or defer to the server.
- More than one or two `useEffect` blocks per component signals logic that should move to a hook.

## Full-Stack

- Share types (or a schema) between client and server; never redeclare shapes that can drift. API calls, types and field constraints come from the generated SDK in `frontend/src/client/` (`bash scripts/generate-client.sh`), called through `lib/api.ts`; never hand-write URLs, API types or copies of backend constraints.
- Keep types strict; avoid `any`/`unknown`/loose dictionaries at API boundaries.
