# Full Stack FastAPI + Next.js 16 Template

A full-stack starter with a FastAPI + PostgreSQL backend and a Next.js 16 (App Router) frontend, wired together with Docker Compose and Traefik.

## Stack

- **Backend** ([`backend/`](backend/)) — FastAPI, SQLModel, PostgreSQL, Alembic, JWT auth, and an AI chat built on [LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) (OpenAI, streamed over [AG-UI](https://docs.ag-ui.com)).
- **Frontend** ([`frontend/`](frontend/)) — Next.js 16 (App Router), React, TypeScript, Tailwind CSS, shadcn/ui on Base UI, and the AI chat on [assistant-ui](https://www.assistant-ui.com).
- **Infra** ([`infra/`](infra/)) — Docker Compose + Traefik, Mailpit for local email, Playwright for end-to-end tests.

## Requirements

[Docker](https://www.docker.com/), [uv](https://docs.astral.sh/uv/), and [Bun](https://bun.sh/).

## Quick Start

From the project root, run:

```bash
./up.sh
```

This resets and rebuilds the stack, runs migrations, and starts it with hot reload. The script prints the app URL and the login to use.

To iterate on one side directly instead, run `uv run fastapi dev` (from `backend/`) or `bun run dev` (from `frontend/`) against the Compose Postgres.

## Configuration

Settings live in `backend/.env`, and `backend/.env.example` lists them. Change the secrets and passwords before deploying anywhere. The AI chat turns on when an OpenAI API key is set.

## API contract

The backend's Pydantic models are the source of truth. After changing them or any route, regenerate the OpenAPI spec and the typed frontend client:

```bash
bash scripts/generate-client.sh
```

The frontend calls the API only through the generated client, and the pre-commit hook, the backend tests and CI fail when it is stale.

## Development

`./up.sh` and `bun install` (in `frontend/`) install the git hooks ([prek](https://github.com/j178/prek)), which run the same checks as the `pre-commit` workflow. Run them on demand with `uv run prek run --all-files`.

## Testing

- Backend: `bash scripts/test.sh` (from the project root).
- Frontend unit tests: `bun run test:unit` (from `frontend/`).
- Frontend end-to-end: `docker compose run --rm playwright bunx playwright test`.

## Deployment

Production runs behind Traefik with automatic HTTPS via `infra/docker-compose.deploy.yml`. Set `DOMAIN` and the secrets as environment variables on the host, then:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.deploy.yml up -d
```

Migrations run automatically before the backend starts. To have a failed migration stop a deploy before anything is replaced, run the `prestart` service first.

If you put a CDN or load balancer in front, set the trusted proxy settings in `infra/docker-compose.deploy.yml`, cache only the landing page and static files, and verify the setup with `bun run check:headers https://your-domain` (from `frontend/`).
