#! /usr/bin/env sh
# Runs the backend tests against a disposable stack.

set -e
set -x

export COMPOSE_FILE=infra/docker-compose.yml:infra/docker-compose.dev.yml
export COMPOSE_ENV_FILES=backend/.env

docker compose down -v --remove-orphans
docker compose up -d db mailpit
(cd backend && uv run bash scripts/prestart.sh)
(cd backend && uv run bash scripts/tests-start.sh "$@")
docker compose down -v --remove-orphans
