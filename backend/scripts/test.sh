#!/usr/bin/env bash

set -e
set -x

FASTAPI_ENV=development coverage run -m pytest tests/
coverage html --fail-under=0 --title "${@-coverage}"
coverage report
