#! /usr/bin/env bash
# Prepares the backend before it starts.

set -e
set -x

python -m src.scripts.wait_for_db

alembic upgrade head

python -m src.scripts.chat_setup

python -m src.scripts.initial_data
