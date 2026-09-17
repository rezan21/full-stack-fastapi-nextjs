#! /usr/bin/env sh

# Exit in case of error
set -e
set -x

export COMPOSE_FILE=infra/docker-compose.yml:infra/docker-compose.dev.yml
export COMPOSE_ENV_FILES=backend/.env

docker compose build
docker compose down -v --remove-orphans # Remove possibly previous broken stacks left hanging after an error
docker compose run --rm backend bash scripts/prestart.sh
docker compose up -d
docker compose exec -T backend bash scripts/tests-start.sh "$@"
docker compose down -v --remove-orphans
