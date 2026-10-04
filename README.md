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

All settings live in `backend/.env`. Change `SECRET_KEY` (at least 32 characters), `FIRST_SUPERUSER_PASSWORD`, `POSTGRES_PASSWORD` (the database administrator) and `APP_DB_PASSWORD` (the limited `app` role the backend connects as) before deploying anywhere; outside development a short or placeholder value stops the backend from starting. The `dbsetup` service creates or updates the `app` role and makes it the owner of the `app` database on every start, so the backend never connects as the superuser and an existing database volume is converted the first time it runs. After `AUTH_MAX_FAILURES` (5) wrong passwords within `AUTH_LOCK_MINUTES` (15) an account answers 429 for that long, whatever the client address; a correct password or a password reset clears the count. The API docs are served only in development.

## API contract

The backend's Pydantic models are the source of truth. After changing them (or any route), regenerate the OpenAPI spec and the typed frontend client:

```bash
bash scripts/generate-client.sh
```

This rewrites `backend/openapi.json` and `frontend/src/client/` (a typed SDK, TypeScript types and Zod schemas). The frontend calls the API only through `frontend/src/lib/api.ts`, a thin adapter over the generated SDK, so URLs, methods and payload types are never typed by hand. The backend test suite and the pre-commit hook fail when the committed files are stale, CI type-checks and builds the frontend, and pull requests that change `backend/openapi.json` are checked for breaking changes (add the `breaking-api-change` label to accept an intentional one).

## Development

`./up.sh` and `bun install` (in `frontend/`) install the git hooks ([prek](https://github.com/j178/prek), configured in `.pre-commit-config.yaml`) when they are missing; `bash scripts/install-hooks.sh` does it on its own. They run the same checks as the `pre-commit` workflow: formatting, spelling, Biome, ruff, mypy, ty, a fresh API client and the skill links. Run them on demand with `uv run prek run --all-files`.

The FastAPI and SQLModel packages ship agent skills. `backend/.agents/skills` and `backend/.claude/skills` link to them inside `backend/.venv`, so the links resolve once `uv sync` has run in `backend/`. After a dependency or Python version change, refresh them from `backend/` with `uv run --project .. library-skills --claude --yes`; the pre-commit hook runs the same tool with `--check`.

## Testing

- Backend: `bash scripts/test.sh` (from the project root); it fails below 90% coverage, and also runs the migration tests against a throwaway database.
- Frontend unit tests: `bun run test:unit` (from `frontend/`); they fail below 90% coverage of the modules they load.
- Frontend end-to-end: `docker compose run --rm playwright bunx playwright test`.

## Deployment

Production runs behind Traefik with automatic HTTPS (Let's Encrypt) via `infra/docker-compose.deploy.yml`. Set `DOMAIN` and the secrets as environment variables on the host, then:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.deploy.yml up -d
```

Adminer is part of the dev stack only and is never deployed. Traefik sends HSTS on every HTTPS response.

Database migrations run automatically, in dev and in production alike: the `prestart` service runs `backend/scripts/prestart.sh` (wait for the database, `alembic upgrade head`, seed the first superuser), and the backend starts only after it succeeds. `up -d` replaces the running backend before the migration runs, so if a migration fails the backend stays down until you fix it. To keep the current version serving when a migration fails, run the migration first, so a failure stops the deploy before anything is replaced:

```bash
docker compose -f infra/docker-compose.yml -f infra/docker-compose.deploy.yml run --rm prestart
```

Then run the `up -d` command above. In dev, run `./up.sh` again after adding a migration so the image is rebuilt with it.

### Behind a CDN

The stack works without one. If you add a CDN or load balancer, three things must hold, and `bun run check:headers` checks the second one:

- **Client address.** Set `TRUSTED_PROXIES` to the CDN's published address ranges (comma-separated CIDRs) and `PROXY_HOPS` to the number of proxies in front of Traefik (1 for a single CDN). Traefik then takes the client address for the rate limit from `X-Forwarded-For`. Keep the ranges current: a request from an address that is not listed loses its forwarded address, and everyone arriving through that edge shares one rate-limit budget. Let the origin accept the CDN only, because a client that connects directly shares one budget with every other direct client. The per-account lockout does not depend on any of this.
- **Caching.** Only static files are cacheable (they are hashed, so `immutable`). Every page is `no-store`, because it depends on the session cookie and carries a Content-Security-Policy nonce that is new for every response. Never turn on a "cache everything" rule for HTML: it would serve one visitor's page to another, with a nonce that does not match. Leave Next's `Cache-Control` headers alone, forward the `rsc` header and keep the query string in the cache key (Next's `_rsc` parameter).
- **Check.** From `frontend/`, run `bun run check:headers https://your-domain`. It verifies that pages are `no-store` with their own nonce and that static files are `immutable`. CI runs the same check against every production build.
