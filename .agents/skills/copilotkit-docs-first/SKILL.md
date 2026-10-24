---
name: copilotkit-docs-first
description: Requires consulting the official CopilotKit docs, and the AG-UI docs for the protocol, before writing or changing CopilotKit code. Use whenever the task touches the CopilotKit runtime or the Next route that serves it, runners, runtime hooks, AG-UI agents and middleware, the React provider and hooks (useAgent, useCopilotKit, useFrontendTool, useRenderTool), frontend tools, generative UI, human-in-the-loop, shared state, AG-UI events, or adding or upgrading @copilotkit/* or @ag-ui/* packages. Also use when a CopilotKit API looks unfamiliar or the user only says "copilot", "CopilotKit", "AG-UI" or "generative UI", because CopilotKit ships two API versions (v1 at the package root, v2 under /v2) and memory of it is often wrong.
---

# CopilotKit docs first

CopilotKit changes quickly and ships two API surfaces. v2 is current and is imported from the `/v2` subpaths (`@copilotkit/react-core/v2`, `@copilotkit/runtime/v2`). The package root is the deprecated v1 surface and still resolves, so mixing the two raises nothing at import time and fails later at runtime. Memory of CopilotKit is often v1 or out of date, so read the current docs before writing CopilotKit code and build from what they say.

## When this applies

Read the docs before you write or change:

- The runtime: `CopilotRuntime`, `createCopilotRuntimeHandler`, its hooks, runners, the routes it serves
- Agents: the AG-UI `HttpAgent`, middleware (`agent.use`), events, errors, cancellation
- The browser side: the provider, `useAgent`, `useCopilotKit`, running and stopping an agent
- Features: frontend tools, tool rendering and other generative UI, human-in-the-loop, shared state, agent context
- The `@copilotkit/*` and `@ag-ui/*` dependency versions

Mechanical edits that touch no CopilotKit or AG-UI API (renaming a variable, fixing copy) don't need a lookup.

## How CopilotKit is used in this repo

- **The browser never reaches FastAPI.** The session cookie is `httpOnly`, so a Next Route Handler serves the runtime at `/copilotkit` (`app/(product)/(app)/copilotkit/[...path]/route.ts`), never under `/api`, which Traefik sends to FastAPI. `proxy.ts` leaves that path to the runtime's own session check.
- **The runtime is built once, in `lib/copilotkit/runtime.ts`.** Its hooks refuse other origins, visitors without a session and non-JSON or oversized bodies, serve only `info` and the `chat` agent's `run` and `stop`, and check that the conversation of a stop belongs to the user.
- **The `chat` agent (`lib/copilotkit/agent.ts`) is an AG-UI `HttpAgent`** that posts through `streamChat` in `lib/api.ts`, so the request carries only the contract's fields and no URL is written by hand. Its middleware drops `MESSAGES_SNAPSHOT`.
- **The runner (`lib/copilotkit/runner.ts`) keeps nothing.** The transcript in Postgres is the only record of a conversation. A refusal from the API becomes a `RUN_ERROR` whose `code` is the HTTP status, and stopping a run, or the browser leaving, aborts the request to FastAPI.
- **The browser** uses the hooks from `@copilotkit/react-core/v2/headless` with our shadcn components, under a `CopilotKitProvider` (from `/v2`) that sends only the newest message (`messageFilter`) and keeps the Inspector off. Runtime telemetry is off (`COPILOTKIT_TELEMETRY_DISABLED` in the `Dockerfile`).
- **FastAPI accepts a browser tool only by name from a server-owned list** (`backend/src/agent/frontend_tools.py`) and ignores client state, context and forwarded props. Letting more through is a backend decision; read `.claude/rules/agentic-design.md` first.

Keep this section true as the integration grows.

## Sources, in order of preference

These are starting points. Follow links and search until you can ground the decision in the docs.

1. **Installed packages**: `frontend/node_modules/@copilotkit/` and `frontend/node_modules/@ag-ui/client` (check each `package.json` for the version; `frontend/package.json` holds ranges). The `.d.mts` files give exact signatures and the `dist` source shows what really happens.
2. **CopilotKit docs MCP** (`copilotkit-mcp` in `.mcp.json`). Its searches are semantic: several short queries with different words beat one long one.
   - `search-docs` for usage, guides and the API reference; `search-code` for how the library implements something
   - `search-ag-ui-docs` and `search-ag-ui-code` for the protocol itself: events, transports, the SDKs
   - `explore-docs` and `explore-code` to browse either tree with `find`, `grep`, `cat` and `ls`
3. **Docs pages as Markdown**: append `.md` to any page path, for example https://docs.copilotkit.ai/backend/copilot-runtime.md. A page that doesn't exist answers 404. Find paths in https://docs.copilotkit.ai/llms.txt (a curated index) or https://docs.copilotkit.ai/sitemap.xml (every page). Never read https://docs.copilotkit.ai/llms-full.txt end to end (about 8 MB); save it to a file and `rg` it. Pages often come in one copy per agent framework; the backend here is a Deep Agent, so prefer the generic pages and those under `/deepagents/`. Pages worth knowing:
   - Runtime: https://docs.copilotkit.ai/backend/copilot-runtime, https://docs.copilotkit.ai/backend/runtime-endpoints, https://docs.copilotkit.ai/backend/agent-runner, https://docs.copilotkit.ai/auth
   - Browser: https://docs.copilotkit.ai/headless, https://docs.copilotkit.ai/reference/hooks/useAgent, https://docs.copilotkit.ai/reference/hooks/useCopilotKit
   - Features: https://docs.copilotkit.ai/deepagents/frontend-tools, https://docs.copilotkit.ai/deepagents/generative-ui/tool-rendering
   - Versions and support: https://docs.copilotkit.ai/migrate/v2, https://docs.copilotkit.ai/troubleshooting/common-issues, https://docs.copilotkit.ai/langgraph-fastapi/telemetry
4. **AG-UI protocol docs**: https://docs.ag-ui.com/llms.txt; its pages take `.md` too, for example https://docs.ag-ui.com/concepts/events.md, https://docs.ag-ui.com/sdk/js/client/http-agent.md and https://docs.ag-ui.com/sdk/js/client/middleware.md.
5. **Source**: https://github.com/CopilotKit/CopilotKit (under `packages/`) and https://github.com/ag-ui-protocol/ag-ui.

## Workflow

1. **Name the API or behavior** in one line (for example, "stop a run from the browser").
2. **Check the surface**: import only from the `/v2` subpaths (the hooks may come from `/v2/headless`). Code that imports from a package root is v1.
3. **Read the matching page** and follow its links, then confirm the exact signature in the installed `.d.mts`.
4. **Write the code from the docs**, not from memory. If they disagree, the docs win; if the docs and the installed source disagree, the installed source is what runs, so build on it and mention the discrepancy.
5. **Verify**: `bun run test:unit` in `frontend/`, then a real run through `http://localhost`.
6. **Cite the pages you used** so the user can check them. If the docs are silent, say the choice is your own judgment. If a docs page looks wrong, offer to report it with the MCP's `submit-feedback`.

## Notes

- Docs describe the latest release; the installed version can lag, so check it when behavior may differ.
- `@ag-ui/client` is pinned to the exact version CopilotKit pins, so one copy is installed. Move them together.
- Don't paste long excerpts into the code or the reply. Summarize, link and apply.
