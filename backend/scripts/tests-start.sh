#! /usr/bin/env bash
# Entry point for the backend tests.
set -e
set -x

python app/tests_pre_start.py

bash scripts/test.sh "$@"
