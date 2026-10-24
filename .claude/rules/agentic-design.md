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
  - "frontend/src/app/**/copilotkit/**"
  - "frontend/src/lib/copilotkit/**"
  - "frontend/src/lib/items-tool*"
  - "frontend/src/lib/place*"
  - "frontend/tests/*chat*"
---

# Agentic Design Rules

## Think from the model's side

- The model is an agent living inside the app, not a function we call. It acts only on its context: the system prompt, the messages, the tool list and the tool results. It cannot see the UI, the clock, the network, or what the user does and sees.
- For every feature that touches the agent, ask from its side: what does it see, what can't it see, and what will it assume where something is missing? It never stays silent: it fills a gap with a plausible guess and states it as fact. After a Stop click, a bare marker made `gpt-5.4-mini` blame a "response limit" in 9 of 9 real answers.
- Anything that changes the agent's situation (a stopped or failed reply, elapsed time, a quota, a missing tool, a permission) must reach its context as a plain fact: what happened, who did it, and what it means. Never leave the agent to infer it.
- The user's view, the transcript and the agent's memory must tell the same story. What the user saw, the agent must have too.
- Teach a convention once in the system prompt and carry each event as data when it happens. Don't list events in the prompt, and don't invent a new channel per feature: reuse the application note (`backend/src/agent/notes.py`).
- Judge a change by how the real model behaves, not by unit tests alone: replay the user's own follow-up questions over several trials and count the right answers. Small models need plainer wording, so test on the model we ship.
- Whatever the user can type, the user can imitate. Never give typed text the standing of an application fact.
- A backend tool takes its user from the run's context (`AgentContext`), never from an argument the model writes, and returns only that user's data. A superuser's assistant sees the superuser's own data, not everyone's.
- The server owns the list of browser tools (`backend/src/agent/frontend_tools.py`): the browser names the ones it can run and the server offers only those it defines. What a browser tool returns is text the user controls, so treat it as data, never as an application fact or an instruction.
- Never print the run's context (the user's id, for one) into the prompt. A library middleware that renders context into the system prompt does exactly that; the one we use has that note switched off, and a test guards it.
