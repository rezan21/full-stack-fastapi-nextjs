---
paths:
  - "backend/src/chat/**"
  - "backend/tests/chat/**"
  - "backend/tests/utils/chat.py"
  - "frontend/src/**/chat/**"
  - "frontend/src/**/*chat*"
  - "frontend/tests/*chat*"
---

# Agentic Design Rules

## Think from the model's side

- The model is an agent living inside the app, not a function we call. It acts only on its context: the system prompt, the messages, the tool list and the tool results. It cannot see the UI, the clock, the network, or what the user does and sees.
- For every feature that touches the agent, ask from its side: what does it see, what can't it see, and what will it assume where something is missing? It never stays silent: it fills a gap with a plausible guess and states it as fact. After a Stop click, a bare marker made `gpt-5.4-mini` blame a "response limit" in 9 of 9 real answers.
- Anything that changes the agent's situation (a stopped or failed reply, elapsed time, a quota, a missing tool, a permission) must reach its context as a plain fact: what happened, who did it, and what it means. Never leave the agent to infer it.
- The user's view, the transcript and the agent's memory must tell the same story. What the user saw, the agent must have too.
- Teach a convention once in the system prompt and carry each event as data when it happens. Don't list events in the prompt, and don't invent a new channel per feature: reuse the application note (`backend/src/chat/notes.py`).
- Judge a change by how the real model behaves, not by unit tests alone: replay the user's own follow-up questions over several trials and count the right answers. Small models need plainer wording, so test on the model we ship.
- Whatever the user can type, the user can imitate. Never give typed text the standing of an application fact.
