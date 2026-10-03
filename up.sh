#!/usr/bin/env bash
set -euo pipefail

export COMPOSE_FILE=infra/docker-compose.yml:infra/docker-compose.dev.yml
export COMPOSE_ENV_FILES=backend/.env

docker info >/dev/null 2>&1 || { echo "❌  Docker isn't running — start Docker Desktop and retry"; exit 1; }

[ -f backend/.env ] || cp backend/.env.example backend/.env

trap 'echo; echo "🛑  Stopping stack..."; kill "${watch_pid:-}" 2>/dev/null || true; docker compose down' INT

superuser=$(grep -E '^FIRST_SUPERUSER=' backend/.env | cut -d= -f2-)
password=$(grep -E '^FIRST_SUPERUSER_PASSWORD=' backend/.env | cut -d= -f2-)

svc_url() {
  local port
  port=$(docker compose port "$1" "$2" 2>/dev/null | tail -1)
  port=${port##*:}
  [ -z "$port" ] && return
  [ "$port" = "80" ] && echo "http://localhost" || echo "http://localhost:$port"
}

echo "🧹  Stopping any existing stack..."
pkill -f "compose watch" 2>/dev/null && sleep 1 || true
docker compose down

echo "🔨  Building images..."
# Docker's build cache occasionally goes stale (dangling snapshot reference); retry once before failing.
docker compose build --quiet || {
  echo "⚠️   Build failed, retrying once..."
  docker compose build --quiet
}

echo "⏳  Starting stack (migrations run before the backend starts)..."
if ! docker compose up -d --wait --wait-timeout 120; then
  echo "❌  A service didn't become healthy:"
  docker compose ps
  docker compose logs --tail 40
  exit 1
fi

echo
echo "🚀  Stack is up with hot reload — press Ctrl+C to stop"
echo "    App        → $(svc_url proxy 80)"
echo "    API docs   → $(svc_url backend 8000)/docs"
echo "    Adminer    → $(svc_url adminer 8080)"
echo "    Mailpit    → $(svc_url mailpit 8025)"
echo "    Login      → ${superuser} / ${password}"
echo

docker compose watch --no-up &
watch_pid=$!

docker compose logs -f --tail 0
