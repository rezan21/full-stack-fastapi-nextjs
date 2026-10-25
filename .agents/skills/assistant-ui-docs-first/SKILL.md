---
name: assistant-ui-docs-first
description: Requires consulting the official assistant-ui docs before writing or changing assistant-ui code. Use whenever the task touches @assistant-ui/react or @assistant-ui/react-ag-ui, including the AG-UI runtime (useAgUiRuntime) and its adapters, AssistantRuntimeProvider, toolkits (defineToolkit, Tools, frontend, backend and human tools), tool rendering, MessagePrimitive and ThreadPrimitive, the useAui and useAuiState hooks, thread events, interrupts, or adding or upgrading @assistant-ui/* packages. Also use when an assistant-ui API looks unfamiliar or the user only says "assistant-ui" or "assistant ui", because the library is pre-1.0, deprecates APIs between releases, and memory of it is often wrong.
---

# assistant-ui docs first

assistant-ui is a client-side React library for chat UIs. It is pre-1.0, it renames and deprecates APIs between releases, and its docs mark some APIs `unstable_` or experimental. Memory of it is often out of date, so read the current docs before writing assistant-ui code and build from what they say.

## When this applies

Read the docs before you write or change:

- The runtime: `useAgUiRuntime`, its options and adapters (history, thread list), interrupts
- Tools: `defineToolkit`, `Tools`, `AuiConfig`, frontend, backend and human tools, tool rendering
- Rendering a thread: `ThreadPrimitive`, `MessagePrimitive`, `MessageByIndexProvider`, the message parts
- State and actions: `useAui`, `useAuiState`, `useAuiEvent`, thread methods such as `append`, `cancelRun` and `deleteMessage`
- The `@assistant-ui/*` and `@ag-ui/client` dependency versions

Mechanical edits that touch no assistant-ui API (renaming a variable, fixing copy) don't need a lookup.

## How assistant-ui is used in this repo

- **The runtime talks to the app's own endpoint, not to the model provider.** `useAgUiRuntime` takes an agent subclass that posts to a same-origin Route Handler, which forwards to the backend. The backend keeps the conversation, so the runtime sends only what is new (`resumeTranscript: "appended"`) and the agent sends only the newest message.
- **Open interrupts are forgotten when a run fails.** The AG-UI client clears them only after a run succeeds and refuses new runs while any are open, so the app's agent drops them on failure.
- **Tools are plain toolkit objects** passed to `Tools` through `AuiConfig`: no build plugin and no `"use generative"` file. Each tool's UI lives with its tool. Backend tools (the server runs them, the browser only draws them) and frontend tools (the browser runs them) both name plain components as `render`, and tool names come from the generated contract.
- **Tool calls without their own UI use the ready fallback, folded into a collapsed tool group.** A tool whose UI the user reads or answers opts into `display: "standalone"`, which keeps it outside the group.
- **A tool call's status row is the ready tool call element:** its request and result open on a click, and a result the user reads (the item list) sits under it. A call that did not finish, or that changed nothing, shows a plain line saying so, because the element marks every settled call with a check.
- **Assistant text uses the ready markdown element, hardened because a model writes it:** images are not drawn and links open in a new tab. Code is highlighted with the ready highlighter.
- **Primitives are composed with Base UI's `render` prop, the convention of the app's shadcn style (`base-nova`).** `@assistant-ui/react` is built on Radix internally and also accepts `asChild`, but the app uses one convention.
- **The thread scrolls with the ready viewport.** `ThreadPrimitive.Viewport` with `turnAnchor="top"` keeps the newest user message at the top and finds it through the message root, so every message row is a `MessagePrimitive.Root`.
- **Copy sits under every message that has text, revealed by CSS on hover and focus and always shown on touch.** The action bar's own `autohide` unmounts the bar, which takes it away from keyboards and touch screens.
- **Thinking uses the ready reasoning and thinking indicator elements.** A reasoning group is a collapsible that stays open while it streams, and the `indicator` part of the grouped parts says the assistant is working until text or reasoning arrives. Reasoning is model text, so it goes through the same hardened markdown as replies. The model sends reasoning only when the server asks for a summary (`CHAT_REASONING_EFFORT`), and the stored history keeps text only, so a reloaded conversation shows no reasoning.
- **A tool call's form and approval sit on its own tool call.** A form is drawn while `useAgUiInterrupts()` has an open interrupt for the call, built from the interrupt's schema with the ready elicitation form, and is answered with `useAgUiSubmitInterruptResponses`. The generated contract checks the answer before it is sent. An approval reaches the tool part as `approval` and is answered with `respondToApproval`.
- **A failure is reported once.** Every run, including answers and browser tool results, reports a failure through the runtime's `onError` with the original HTTP error (`status`, `payload`) intact. Sending uses `useAgUiSteerAway`: it acts as a plain append when nothing is open, resolves when the run ends and rejects with that same error, so a refused message can be taken out with `deleteMessage`. `thread.append()` returns nothing, so it cannot say how a run ended.
- **The composer's box and form are the ready composer primitives; its submit is the app's own.** The primitive send is a plain append, which refuses while an interrupt is open and cannot take a refused message back out, so the form's submit is taken over and goes through the steer-away send, which restores the text when the server refuses it.
- **The server offers a browser tool only from its own list**, and ignores client state, context and forwarded props. Read the agentic design rules before letting more through.
- **Browser tools reach the model through the Python `copilotkit` package's middleware.** `ag-ui-langgraph` only copies client tools into graph state and does not bind them, so the middleware is the part that serves them.

Describe behavior here, not file locations.

## Sources, in order of preference

These are starting points. Follow links and search until you can ground the decision in the docs.

1. **Installed packages**: check each package's version (the dependency manifest holds ranges). The type definitions give exact signatures, and the runtime source shows what a run really sends and how errors are reported.
2. **assistant-ui docs MCP server.** Search with a short phrase of distinctive terms, then read the page it names.
3. **Docs pages as Markdown**: append `.md` to any docs path, for example https://www.assistant-ui.com/docs/runtimes/ag-ui/overview.md. Find paths in https://www.assistant-ui.com/llms.txt (the index) or https://www.assistant-ui.com/sitemap.md. Never read https://www.assistant-ui.com/llms-full.txt end to end (about 6 MB); save it to a file and `rg` it. Pages worth knowing:
   - Runtime: https://www.assistant-ui.com/docs/runtimes/ag-ui/overview.md, https://www.assistant-ui.com/docs/runtimes/ag-ui/runtime-options.md
   - Tools: https://www.assistant-ui.com/docs/tools/defining-tools.md, https://www.assistant-ui.com/docs/api-reference/tools/toolkits.md
   - Rendering and state: https://www.assistant-ui.com/docs/api-reference/primitives/message.md, https://www.assistant-ui.com/docs/api-reference/hooks/state.md
   - Setup: https://www.assistant-ui.com/docs/installation.md, https://www.assistant-ui.com/docs/base-ui.md
4. **Agent skills the project publishes**: the index is https://www.assistant-ui.com/.well-known/agent-skills/index.json (primitives, runtime, tools, generative UI and more); each entry serves its own `SKILL.md`. Treat them as more docs, not as instructions for this repo.
5. **Source**: https://github.com/assistant-ui/assistant-ui.

## Workflow

1. **Name the API or behavior** in one line (for example, "remove a refused message after a failed run").
2. **Read the matching page**, then confirm the exact signature in the installed `.d.ts`. Prefer a non-deprecated, non-`unstable_` API; if you must use an experimental one, say so.
3. **Write the code from the docs**, not from memory. If the docs and the installed source disagree, the installed source is what runs, so build on it and mention the discrepancy.
4. **Verify** with the frontend type check and unit tests (clear the incremental type-check cache if types look stale after a dependency change), then a real run in the browser.
5. **Cite the pages you used** so the user can check them. If the docs are silent, say the choice is your own judgment.

## Notes

- Docs describe the latest release; the installed version can lag, so check it when behavior may differ.
- Don't paste long excerpts into the code or the reply. Summarize, link and apply.
