#! /bin/bash

# Check for updates by comparing the current git hash with the latest git hash
# on the main branch. If there is a difference, update the system.

set -euo pipefail

# Ensure the script is run from the correct directory
cd "$(dirname "$0")/.."

current_hash=$(git rev-parse HEAD)
latest_hash=$(git ls-remote origin -h refs/heads/main | cut -f1)

if [ "$current_hash" != "$latest_hash" ]; then
    echo "Application update available. Updating to commit hash ${latest_hash}..."
    git pull || { echo "Failed to pull latest changes"; exit 1; }
    ../../update-app-user.sh || { echo "Failed to run update script"; exit 1; }
    echo "Application updated."
else
    echo "Application is up to date at commit hash ${current_hash}."
fi
