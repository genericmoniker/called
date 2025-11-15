#!/bin/bash

# Update the application in production (run as root).
# This script should be idempotent.
set -euo pipefail

DOMAIN="$1"
if [ -z "$DOMAIN" ]; then
    echo "Usage: $0 <my-domain.com>"
    exit 1
fi

REPO_DIR="/home/app-user/called"

# Install systemd units if not already installed or updated.
for unit_file in "$REPO_DIR/deployment/server/systemd"/*; do
    if [ -f "$unit_file" ]; then
        unit_name=$(basename "$unit_file")
        dest_file="/etc/systemd/system/$unit_name"

        # Install if doesn't exist or source is newer
        if [ ! -f "$dest_file" ] || [ "$unit_file" -nt "$dest_file" ]; then
            cp "$unit_file" "$dest_file"
            systemctl daemon-reload
            systemctl enable --now "$unit_name"
            echo "Installed and enabled $unit_name"
        fi
    fi
done

# Configure nginx (idempotent)
src_nginx_conf="$REPO_DIR/deployment/server/called-nginx.conf"
dst_nginx_conf="/etc/nginx/sites-available/called"

if [ ! -f /etc/nginx/sites-available/called ]; then
    cp "$src_nginx_conf" "$dst_nginx_conf"
    sed -i "s/{domain}/$DOMAIN/g" "$dst_nginx_conf"  # Replace placeholder with actual domain name.
fi

# Enable site if not already enabled
if [ ! -L /etc/nginx/sites-enabled/called ]; then
    ln -s /etc/nginx/sites-available/called /etc/nginx/sites-enabled/called
fi

# Disable default site if it exists
if [ -L /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Configure firewall (idempotent - ufw handles this gracefully)
ufw allow 80/tcp   # Allow HTTP (needed for certbot)
ufw allow 443/tcp  # Allow HTTPS

# Set up TLS with certbot (idempotent)
certbot --nginx  --non-interactive --agree-tos
