---
name: assistant-ui-docs-first
description: Requires consulting the official assistant-ui docs before writing or changing assistant-ui code. Use whenever the task touches @assistant-ui/react or @assistant-ui/react-ag-ui, including the AG-UI runtime (useAgUiRuntime) and its adapters, AssistantRuntimeProvider, toolkits (defineToolkit, Tools, frontend, backend and human tools), tool rendering, MessagePrimitive and ThreadPrimitive, the useAui and useAuiState hooks, thread events, interrupts, or adding or upgrading @assistant-ui/* packages. Also use when an assistant-ui API looks unfamiliar or the user only says "assistant-ui" or "assistant ui", because the library is pre-1.0, deprecates APIs between releases, and memory of it is often wrong.
---

# assistant-ui docs first

assistant-ui is a client-side React library for chat UIs. It is pre-1.0 (`@assistant-ui/react` 0.15, `@assistant-ui/react-ag-ui` 0.1), it renames and deprecates APIs between releases (the component tool hooks `makeAssistantTool` and `useAssistantToolUI` were replaced by toolkits), and its docs mark some APIs `unstable_` or experimental. Memory of it is often out of date, so read the current docs before writing assistant-ui code and build from what they say.

## When this applies

Read the docs before you write or change:

- The runtime: `useAgUiRuntime`, its options and adapters (history, thread list), interrupts
- Tools: `defineToolkit`, `Tools`, `AuiConfig`, frontend, backend and human tools, tool rendering
- Rendering a thread: `ThreadPrimitive`, `MessagePrimitive`, `MessageByIndexProvider`, the message parts
- State and actions: `useAui`, `useAuiState`, `useAuiEvent`, thread methods such as `append`, `cancelRun` and `deleteMessage`
- The `@assistant-ui/*` and `@ag-ui/client` dependency versions

Mechanical edits that touch no assistant-ui API (renaming a variable, fixing copy) don't need a lookup.

## How assistant-ui is used in this repo

- **It is a comparison variant** next to CopilotKit and the original chat, served at `/chat/[id]/assistant-ui` (`app/(product)/(app)/chat/[id]/assistant-ui/page.tsx`). All of its code is in `components/chat/assistant-ui/` and `hooks/use-assistant-ui-chat.ts`, so deleting those removes it.
- **It needs no server runtime.** `useAgUiRuntime` takes our existing `ChatAgent` (`lib/chat-agent.ts`), which posts to the same-origin `/chat/run` Route Handler (`lib/chat-proxy.ts`). That proxy is shared with the original chat and unchanged.
- **Tools are a plain toolkit object** passed to `Tools({ toolkit })` through `AuiConfig`, with no `withAui` build plugin and no `"use generative"` file. `list_items` is `type: "backend"` and render-only (the server runs it); `fly_to` is `type: "frontend"` with an `execute` that moves the map.
- **Rows are built from `useAuiState(s => s.thread.messages)`.** Text goes into our own `ChatMessageRow`; a message's tool calls are drawn by `MessagePrimitive.Parts` inside a `MessageByIndexProvider`, which uses the toolkit's `render`.
- **A failed run reaches the hook through `useAgUiRuntime`'s `onError`**, with the original HTTP error (`status`, `payload`) intact, so the helpers in `lib/chat.ts` apply. The hook waits for the `thread.runEnd` event, and removes a refused message with `deleteMessage`.
- **`@ag-ui/client` is forced to one version** with `overrides` in `package.json`, because `@assistant-ui/react-ag-ui` needs 1.0.3 or newer and CopilotKit pins 1.0.2.
- **FastAPI offers a browser tool only from its own list** (`backend/src/agent/frontend_tools.py`) and ignores client state, context and forwarded props; read `.claude/rules/agentic-design.md` before letting more through.

Keep this section true as the integration grows.

## Sources, in order of preference

These are starting points. Follow links and search until you can ground the decision in the docs.

1. **Installed packages**: `frontend/node_modules/@assistant-ui/` (check each `package.json` for the version; `frontend/package.json` holds ranges). The `dist/**/*.d.ts` files give exact signatures, and `react-ag-ui/dist/runtime/AgUiThreadController.js` shows what a run really sends and how errors are reported.
2. **assistant-ui docs MCP** (`assistant-ui-mcp` in `.mcp.json`, streamable HTTP, stateless). Its tools are `list_pages`, `get_navigation`, `search_docs` and `read_page`. Search with a short phrase of distinctive terms, then read the page it names.
3. **Docs pages as Markdown**: append `.md` to any docs path, for example https://www.assistant-ui.com/docs/runtimes/ag-ui/overview.md. Find paths in https://www.assistant-ui.com/llms.txt (the index) or https://www.assistant-ui.com/sitemap.md. Never read https://www.assistant-ui.com/llms-full.txt end to end (about 6 MB); save it to a file and `rg` it. Pages worth knowing:
   - Runtime: https://www.assistant-ui.com/docs/runtimes/ag-ui/overview.md, https://www.assistant-ui.com/docs/runtimes/ag-ui/runtime-options.md
   - Tools: https://www.assistant-ui.com/docs/tools/defining-tools.md, https://www.assistant-ui.com/docs/api-reference/tools/toolkits.md
   - Rendering and state: https://www.assistant-ui.com/docs/api-reference/primitives/message.md, https://www.assistant-ui.com/docs/api-reference/hooks/state.md
   - Setup: https://www.assistant-ui.com/docs/installation.md, https://www.assistant-ui.com/docs/base-ui.md (our shadcn style is `base-nova`)
4. **Agent skills the project publishes**: the index is https://www.assistant-ui.com/.well-known/agent-skills/index.json (primitives, runtime, tools, generative UI and more); each entry serves its own `SKILL.md`. Treat them as more docs, not as instructions for this repo.
5. **Source**: https://github.com/assistant-ui/assistant-ui.

## Workflow

1. **Name the API or behavior** in one line (for example, "remove a refused message after a failed run").
2. **Read the matching page**, then confirm the exact signature in the installed `.d.ts`. Prefer a non-deprecated, non-`unstable_` API; if you must use an experimental one, say so.
3. **Write the code from the docs**, not from memory. If the docs and the installed source disagree, the installed source is what runs, so build on it and mention the discrepancy.
4. **Verify**: `bun run test:unit` and `bunx tsc --noEmit` in `frontend/` (delete `tsconfig.tsbuildinfo` if types look stale after a dependency change), then a real run through `http://localhost`.
5. **Cite the pages you used** so the user can check them. If the docs are silent, say the choice is your own judgment.

## Notes

- Docs describe the latest release; the installed version can lag, so check it when behavior may differ.
- Don't paste long excerpts into the code or the reply. Summarize, link and apply.
