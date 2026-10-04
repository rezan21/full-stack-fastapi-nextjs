#!/bin/sh -e
# Formats the backend.
set -x

ruff check app scripts --fix
ruff format app scripts
