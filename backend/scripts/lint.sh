#!/usr/bin/env bash
# Lints and type-checks the backend.

set -e
set -x

mypy app
ty check app
ruff check app
ruff format app --check
