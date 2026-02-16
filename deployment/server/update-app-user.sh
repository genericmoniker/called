#!/bin/bash

# Update the application in production (run as app-user).
# Look on the server for /var/log/cloud-init-output.log to see the output of this script.

set -euox pipefail

echo "------------------------------ update-app-user.sh ------------------------------"

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

# Install/update systemd service
mkdir -p ~/.config/systemd/user
cp ./deployment/server/systemd/*.service ~/.config/systemd/user/
cp ./deployment/server/systemd/*.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now called-update.timer
