#! /usr/bin/env bash
# Entry point for the backend tests.
set -e
set -x

python -m src.scripts.wait_for_db

bash scripts/test.sh "$@"
