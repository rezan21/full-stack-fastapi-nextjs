#! /usr/bin/env sh

# Exit in case of error
set -e
set -x

export COMPOSE_FILE=infra/docker-compose.yml:infra/docker-compose.dev.yml
export COMPOSE_ENV_FILES=backend/.env

docker compose down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error
docker compose up -d db mailpit
(cd backend && uv run bash scripts/prestart.sh)
(cd backend && uv run bash scripts/tests-start.sh "$@")
docker compose down -v --remove-orphans
