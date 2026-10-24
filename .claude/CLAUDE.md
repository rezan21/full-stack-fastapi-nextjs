# CLAUDE.md

- [CLAUDE.md](#claudemd)
  - [General Instructions](#general-instructions)
    - [1. Think Before Coding](#1-think-before-coding)
    - [2. Simplicity First](#2-simplicity-first)
    - [3. Surgical Changes](#3-surgical-changes)
    - [4. Goal-Driven Execution](#4-goal-driven-execution)
    - [5. Consistent and Idiomatic](#5-consistent-and-idiomatic)
  - [Next js 16](#next-js-16)
  - [IMPORTANT RULES](#important-rules)

Important instructions for you, the LLM/Agent/Claude.

## General Instructions

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

### 5. Consistent and Idiomatic

**One way to do each thing, applied everywhere. Use each tool the way it was designed to be used.**

Before choosing a pattern (import direction, naming, file layout, error handling, test style):

- Find how the codebase already does it and reuse that. If there is no precedent, choose deliberately and apply it everywhere it applies, in the same change.
- Never leave two ways to do the same thing. Either migrate every instance of a pattern or don't introduce the new one.
- Keep dependencies pointing one way: a lower layer never imports a higher one. Pin the direction with a test when it can be checked mechanically.
- Use one name per concept across code, tests, config and docs. Rename the whole set or none of it.
- For a library or framework, use its documented mechanism, read from the current official docs rather than from memory. If the docs are silent, or you must work around the library, say so, keep the workaround in one place and cover it with a test.

Before finishing, search for both the old and the new form of whatever you changed. No half-migrated leftovers in code, tests, scripts, config or docs.

The test: a reader can't tell which parts were written first.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, clarifying questions come before implementation rather than after mistakes, and new code reads as if one hand wrote all of it.

## Next js 16

<!-- BEGIN:nextjs-agent-rules -->

**This is NOT the Next.js you know**

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `frontend/node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.

<!-- END:nextjs-agent-rules -->

## IMPORTANT RULES

- never git commit nor push automatically, unless explicitly asked. confirm with user.
- do not create documentation or markdown files unless explicitly asked.
