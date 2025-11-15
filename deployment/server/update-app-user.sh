#!/bin/bash

# Update the application in production (run as app-user).

set -euo pipefail

# Ensure uv is in PATH
source ~/.local/bin/env

cd ~/called

# Install/update dependencies
uv self update
uv sync

# Run database migrations
uv run manage.py migrate

# Collect static files
uv run manage.py collectstatic --noinput
