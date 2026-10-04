#! /usr/bin/env sh
# Runs the backend tests against a disposable database that is separate from the dev stack.

set -e

export COMPOSE_FILE=infra/docker-compose.yml:infra/docker-compose.dev.yml
export COMPOSE_ENV_FILES=backend/.env
export COMPOSE_PROJECT_NAME=full-stack-fastapi-nextjs-test
export DB_PORT=55432

set -a
. backend/.env
set +a
export DATABASE_URL="postgresql://app:${APP_DB_PASSWORD}@localhost:${DB_PORT}/app"

set -x
docker compose down -v --remove-orphans
docker compose up -d db
docker compose run --rm dbsetup
(cd backend && uv run bash scripts/prestart.sh)
(cd backend && uv run bash scripts/tests-start.sh "$@")
docker compose down -v --remove-orphans
