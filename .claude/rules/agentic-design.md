---
paths:
  - "backend/src/agent/**"
  - "backend/src/chat/**"
  - "backend/tests/agent/**"
  - "backend/tests/chat/**"
  - "backend/tests/utils/agent.py"
  - "backend/tests/utils/chat.py"
  - "frontend/src/**/chat/**"
  - "frontend/src/**/*chat*"
  - "frontend/src/lib/*-tool*"
  - "frontend/tests/*chat*"
---

# Agentic Design Rules

## Think from the model's side

- The model is an agent living inside the app, not a function we call. It acts only on its context: the system prompt, the messages, the tool list and the tool results. It cannot see the UI, the clock, the network, or what the user does and sees.
- For every feature that touches the agent, ask from its side: what does it see, what can't it see, and what will it assume where something is missing? It never stays silent: it fills a gap with a plausible guess and states it as fact. After a Stop click, a bare marker made `gpt-5.4-mini` blame a "response limit" in 9 of 9 real answers.
- Anything that changes the agent's situation (a stopped or failed reply, elapsed time, a quota, a missing tool, a permission) must reach its context as a plain fact: what happened, who did it, and what it means. Never leave the agent to infer it.
- The user's view, the transcript and the agent's memory must tell the same story. What the user saw, the agent must have too.
- Teach a convention once in the system prompt and carry each event as data when it happens. Don't list events in the prompt, and don't invent a new channel per feature: reuse the application note.
- Judge a change by how the real model behaves, not by unit tests alone: replay the user's own follow-up questions over several trials and count the right answers. Small models need plainer wording, so test on the model we ship.
- Whatever the user can type, the user can imitate. Never give typed text the standing of an application fact.
- A backend tool takes its user from the run's context, never from an argument the model writes, and returns only that user's data. A superuser's assistant sees the superuser's own data, not everyone's.
- A tool is one self-contained module. One registry lists the modules, and everything derived from them (the agent's tools, the browser's tools, the shared models, the published tool names) comes from that registry, so nothing is listed twice by hand.
- The server owns the list of browser tools: the browser names the ones it can run and the server offers only those it defines. The client gets the tool names from the published spec. What a browser tool returns is text the user controls, so treat it as data, never as an application fact or an instruction.
- The model calls one tool at a time. A run carries one new input, either the user's message, a browser tool's result or the answers to the open interrupts, so a turn holds one outstanding call, whether it waits for the browser or for the user.
- A tool that changes the user's data pauses for the user. Deletes ask for approval, and the server writes the question from the stored data, never from the model's words. Creating and editing act directly once they have the details; a form asks only for the details that are missing, so the model never invents them. Each answer reaches the model as a fact: approved, declined, submitted or cancelled. Only an answer to an interrupt the server has open is accepted, and a new message closes the open interrupts. An answer that comes with a message or a tool result is refused, so no answer is dropped silently.
- Never print the run's context (the user's id, for one) into the prompt. A library middleware that renders context into the system prompt does exactly that; the one we use has that note switched off, and a test guards it.
