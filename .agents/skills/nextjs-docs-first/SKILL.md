---
name: nextjs-docs-first
description: Requires consulting the official Next.js 16 docs and the next-devtools MCP before writing or changing Next.js code. Use whenever the task touches the App Router, including routing, layouts, pages, Server vs Client Components, Server Actions, data fetching, caching and revalidation, proxy.ts, metadata, route handlers, next.config, params and searchParams, cookies and headers, error, loading and not-found files, Turbopack, or upgrading next. Also use when a Next.js API looks unfamiliar or the user only says "Next", "app router", "RSC", or "server action", because Next.js 16 has breaking changes and memory of older versions is often wrong.
---

# Next.js docs first

Next.js 16 changed APIs, conventions, and file structure (for example `proxy.ts` replaced `middleware.ts`, and `params` and `searchParams` are promises). Training-data memory of Next.js is often out of date, so read the current docs before writing Next.js-specific code and build from what they say.

## When this applies

Read the docs before you write or change:

- Routing and file conventions: `page`, `layout`, `loading`, `error`, `not-found`, `route`, `proxy`, dynamic segments
- Rendering: Server and Client Components, streaming, `"use client"` boundaries
- Data and mutations: fetching, Server Actions, forms, caching, revalidation
- Config and tooling: `next.config`, Turbopack, environment variables, metadata, upgrading `next`

Mechanical edits that touch no Next.js API (renaming a variable, fixing copy) don't need a lookup.

## Sources, in order of preference

These are starting points. Follow links and search until you can ground the decision in the docs.

1. **Docs bundled with the installed version**: `frontend/node_modules/next/dist/docs/` (markdown, matches the installed `next` version exactly). App Router pages live under `01-app/`: guides in `02-guides/` (breaking changes in `02-guides/upgrading/version-16.md`), APIs in `03-api-reference/` (`03-file-conventions/`, `04-functions/`, `05-config/`). Find pages with `rg -il "keyword" frontend/node_modules/next/dist/docs/` instead of guessing paths. If `node_modules` is missing, run `bun install` in `frontend/` or use the web docs below.
2. **next-devtools MCP** (`next-devtools` in `.mcp.json`):
   - `nextjs_docs` returns where the bundled docs live.
   - `nextjs_index` lists running dev servers and their tools; `nextjs_call` runs one (`get_errors`, `get_routes`, `get_compilation_issues`, `compile_route`, `get_page_metadata`, `get_logs`). These need a running `next dev`; pass `port` if discovery finds nothing.
   - To check a change in the real app, use the `next-dev-loop` skill.
3. **Official web docs**, when the bundled copy is missing or the question concerns a newer release (the site tracks the latest 16.x, which can be ahead of the installed version):
   - https://nextjs.org/docs (docs home)
   - https://nextjs.org/docs/app/api-reference (exact signatures, props, config options)
   - https://nextjs.org/llms.txt (how to read the site efficiently)
   - https://nextjs.org/docs/llms.txt (index of every page, good for discovering the right one)
   - https://nextjs.org/docs/llms-full.txt (the whole corpus, about 4 MB: never read it end to end; save it to a file and `rg` it)

   Append `.md` to any docs URL, or send `Accept: text/markdown`, to get markdown instead of HTML. Use `/docs/app/` pages, not `/docs/pages/`: this project uses the App Router.

## Workflow

1. **Name the API or behavior** in one line (for example, "revalidate the layout after a Server Action").
2. **Read the matching page** from the bundled docs and follow its links. Guides explain how things fit together; the API reference has the exact signatures.
3. **Write the code from the docs**, not from memory. If they disagree, the docs win; mention the discrepancy.
4. **Verify after editing**: `get_errors` and `get_compilation_issues` through the MCP, or the `next-dev-loop` skill for runtime behavior.
5. **Cite the pages you used** in your reply or plan so the user can check them. If the docs are silent, say the choice is your own judgment.

## Notes

- Check the installed version (`frontend/node_modules/next/package.json`; `frontend/package.json` only holds a range) when behavior may depend on it.
- Don't paste long doc excerpts into the codebase or the reply. Summarize, link, and apply.
