#!/bin/bash

# Update the application in production (run as app-user).

set -euox pipefail

# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

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
