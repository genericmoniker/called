#!/bin/bash
set -euo pipefail

REPODIR="$(cd "$(dirname "$(dirname "${BASH_SOURCE[0]}")")" && pwd)"
cd "$REPODIR"

uv run deployment/server/do-deploy.py
