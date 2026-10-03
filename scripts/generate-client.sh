#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

PROJECT_NAME="FastAPI Template" \
SECRET_KEY=openapi-export \
FIRST_SUPERUSER=admin@example.com \
FIRST_SUPERUSER_PASSWORD=openapi-export \
DATABASE_URL=postgresql://user:openapi-export@localhost:5432/app \
  uv run --project backend python -c \
  'import json; from app.main import app; print(json.dumps(app.openapi(), indent=2, sort_keys=True))' \
  > backend/openapi.json.tmp
mv backend/openapi.json.tmp backend/openapi.json

(cd frontend && bun run generate-client)
