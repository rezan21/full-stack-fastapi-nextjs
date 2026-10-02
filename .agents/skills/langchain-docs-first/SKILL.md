---
name: langchain-docs-first
description: Requires consulting the official LangChain docs before any architectural decision involving LangChain, LangGraph, or Deep Agents. Use whenever the task touches AI agents built with these libraries — choosing between create_agent, LangGraph, and create_deep_agent, designing agent graphs, state, checkpointers, memory, subagents, middleware, tools or MCP integration, human-in-the-loop, backends or sandboxes, streaming, or deployment. Also use when adding or upgrading langchain, langgraph, or deepagents dependencies, or when an API is unfamiliar. Make sure to use this skill even if the user only says "agent", "deep agent", "graph", or "workflow" and the stack is LangChain-based, because these libraries change fast and memory of their APIs is often stale.
---

# LangChain docs first

LangChain, LangGraph, and Deep Agents move quickly. APIs get renamed, defaults change (for example, Deep Agents task planning became opt-in in v0.7), and the right layer to build on shifts. Training-data memory of these libraries is often out of date, so for anything that shapes the architecture, read the current official docs first and build from what they say.

## When this applies

Read the docs before you commit to any of these:

- Which layer to build on: `create_deep_agent`, LangChain `create_agent`, or a custom LangGraph graph
- Agent or graph structure: nodes, edges, state schema, subagents, delegation, multi-agent patterns
- Persistence and context: checkpointers, stores, memory, summarization, filesystem backends
- Control and safety: human-in-the-loop, interrupts, permissions, sandboxes, code execution
- Tools and integrations: custom tools, MCP servers, middleware, streaming, deployment
- Adding or bumping `langchain`, `langgraph`, or `deepagents` dependencies

Small, mechanical edits inside an already-designed agent (renaming a variable, fixing a typo in a prompt) don't need a docs lookup.

## Sources, in order of preference

These are starting points, not the full scope of the lookup. The overview pages are entry points; the answer to a specific decision usually lives in a linked guide or a page the overviews don't mention. Follow links, search the MCP, and crawl related pages as needed until you can ground the decision in the docs.

1. **LangChain docs MCP.** If the `lanchain-mcp` server is available, use its tools; they return current content and are cheaper than fetching pages.
   - `search_docs_by_lang_chain` for conceptual questions ("how do subagents work", "checkpointer options")
   - `query_docs_filesystem_docs_by_lang_chain` to read a full page or grep for exact terms. Pages live at `<url-path>.mdx`, for example `/oss/python/deepagents/overview.mdx`. Never guess paths; find them with search or `rg -il "keyword" /` first.
2. **The official pages**, as the minimum baseline when the MCP is unavailable or does not cover the question. Start from the one that matches the layer you are working in, then branch out to related pages:
   - Deep Agents: https://docs.langchain.com/oss/python/deepagents/overview
   - LangChain: https://docs.langchain.com/oss/python/langchain/overview
   - LangGraph (lower level): https://docs.langchain.com/oss/python/langgraph/overview
   - API reference, when you need exact signatures, parameters, or types: https://docs.langchain.com/oss/python/reference/overview
   - Larger reference pages, useful when you need broad coverage or don't know which page to open. They are big, so search or skim them for the relevant section instead of reading end to end:
     - https://docs.langchain.com/llms.txt (site-wide index of doc pages, good for discovering pages the overviews don't link to)
     - https://docs.langchain.com/_llms/agent-development-lifecycle/build/python.md (consolidated Python build reference)

Use the Python docs (`/oss/python/`) unless the project is TypeScript, in which case swap in `/oss/javascript/`.

## Workflow

1. **Name the decision.** State in one line what architectural choice is being made (for example, "single agent with tools vs. Deep Agents with subagents").
2. **Read the matching overview**, then follow links into the specific guide (subagents, backends, persistence, human-in-the-loop, and so on). The overview pages are maps; the decisions are usually in the linked guides.
3. **Check the API reference** before writing code that calls specific functions or classes. Signatures and parameter names are the things most likely to have changed.
4. **Pick the layer deliberately.** The docs position these as a stack: LangChain provides building blocks, LangGraph is the runtime, and Deep Agents is a batteries-included harness on top. Prefer the highest layer that fits the need and drop down only when the higher one can't express it. Say which you chose and why.
5. **Cite what you used.** In your reply or plan, name the doc pages that informed the decision so the user can verify them. If the docs and your prior knowledge disagree, the docs win; mention the discrepancy.
6. **Say so when the docs are silent.** If nothing in the docs covers the question, flag the choice as your own judgment rather than implying it is documented best practice. If a docs page looks wrong or outdated and the MCP offers `submit_feedback`, offer to report it.

## Notes

- Look up the installed package version (`uv pip show deepagents`, or check `pyproject.toml`) when behavior might depend on it; docs describe the latest release.
- Don't paste long doc excerpts into the codebase or reply. Summarize, link, and apply.
