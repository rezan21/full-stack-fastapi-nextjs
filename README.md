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

## API contract

The backend's Pydantic models are the source of truth. After changing them (or any route), regenerate the OpenAPI spec and the typed frontend client:

```bash
bash scripts/generate-client.sh
```

This rewrites `backend/openapi.json` and `frontend/src/client/` (a typed SDK, TypeScript types and Zod schemas). The frontend calls the API only through `frontend/src/lib/api.ts`, a thin adapter over the generated SDK, so URLs, methods and payload types are never typed by hand. The backend test suite and the pre-commit hook fail when the committed files are stale, CI type-checks and builds the frontend, and pull requests that change `backend/openapi.json` are checked for breaking changes (add the `breaking-api-change` label to accept an intentional one).

## Development

The FastAPI and SQLModel packages ship agent skills. `backend/.agents/skills` and `backend/.claude/skills` link to them inside `backend/.venv`, so the links resolve once `uv sync` has run in `backend/`. After a dependency or Python version change, refresh them from `backend/` with `uv run --project .. library-skills --claude --yes`; the pre-commit hook runs the same tool with `--check`.

## Testing

- Backend: `bash scripts/test.sh` (from the project root).
- Frontend end-to-end: `docker compose run --rm playwright bunx playwright test`.

## Deployment

Production runs behind Traefik with automatic HTTPS (Let's Encrypt) via `infra/docker-compose.deploy.yml`. Set `DOMAIN` and the secrets as environment variables on the host, then:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.deploy.yml up -d
```

Database migrations run automatically, in dev and in production alike: the `prestart` service runs `backend/scripts/prestart.sh` (wait for the database, `alembic upgrade head`, seed the first superuser), and the backend starts only after it succeeds. `up -d` replaces the running backend before the migration runs, so if a migration fails the backend stays down until you fix it. To keep the current version serving when a migration fails, run the migration first, so a failure stops the deploy before anything is replaced:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.deploy.yml run --rm prestart
```

Then run the `up -d` command above. In dev, run `./up.sh` again after adding a migration so the image is rebuilt with it.
