#! /usr/bin/env bash
# Prepares the backend before it starts.

set -e
set -x

python app/backend_pre_start.py

alembic upgrade head

python app/chat_setup.py

python app/initial_data.py
