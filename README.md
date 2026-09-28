# Full Stack FastAPI + Next.js 16 Template

A full-stack starter with a FastAPI + PostgreSQL backend and a Next.js 16 (App Router) frontend, wired together with Docker Compose and Traefik.

## Stack

- **Backend** ([`backend/`](backend/)) — FastAPI, SQLModel, PostgreSQL, Alembic, JWT auth.
- **Frontend** ([`frontend/`](frontend/)) — Next.js 16 (App Router), React, TypeScript, Tailwind CSS, shadcn/ui.
- **Infra** ([`infra/`](infra/)) — Docker Compose + Traefik, Mailpit for local email, Playwright for end-to-end tests.

## Requirements

[Docker](https://www.docker.com/), [uv](https://docs.astral.sh/uv/), and [Bun](https://bun.sh/).

## Quick Start

From the project root, run:

```bash
./up.sh
```

This resets and rebuilds the stack, runs migrations, and starts it with hot reload. The app is served through the Traefik proxy at <http://localhost>; the script prints the login to use.

Local URLs: API docs <http://localhost/docs> · Adminer <http://localhost:8080> · Mailpit <http://localhost:8025> · Traefik dashboard <http://localhost:8090>.

To iterate on one side directly instead, run `uv run fastapi dev` (from `backend/`) or `bun run dev` (from `frontend/`) against the Compose Postgres.

## Configuration

All settings live in `backend/.env`. Change `SECRET_KEY`, `FIRST_SUPERUSER_PASSWORD`, and `POSTGRES_PASSWORD` before deploying anywhere.

## Testing

- Backend: `bash scripts/test.sh` (from the project root).
- Frontend end-to-end: `docker compose run --rm playwright bunx playwright test`.

## Deployment

Production runs behind Traefik with automatic HTTPS (Let's Encrypt) via `infra/docker-compose.deploy.yml`. Set `DOMAIN` and the secrets as environment variables on the host, then:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.deploy.yml up -d
```
