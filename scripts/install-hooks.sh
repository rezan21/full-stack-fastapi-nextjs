#!/usr/bin/env bash
# Installs the git hooks when they are missing.
set -euo pipefail

cd "$(dirname "$0")/.."

[ -z "${CI:-}" ] || exit 0
command -v uv >/dev/null || exit 0
hook=$(git rev-parse --git-path hooks/pre-commit 2>/dev/null) || exit 0

if [ ! -f "$hook" ]; then
  echo "🪝  Installing git hooks (prek)..."
  uv run prek install >/dev/null
fi
