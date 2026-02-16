#!/bin/bash

# Update the application in production (run as root).
# This script should be idempotent.
# Look on the server for /var/log/cloud-init-output.log to see the output of this script.
set -euox pipefail

echo "------------------------------ update-root.sh ------------------------------"


DOMAIN_NAME="$1"
if [ -z "$DOMAIN_NAME" ]; then
    echo "Usage: $0 <my-domain.com>"
    exit 1
fi

REPO_DIR="/home/app-user/called"

# Configure nginx (idempotent)
src_nginx_conf="$REPO_DIR/deployment/server/called-nginx.conf"
dst_nginx_conf="/etc/nginx/sites-available/called"
tmp_nginx_conf="$(mktemp)"

cp "$src_nginx_conf" "$tmp_nginx_conf"
sed -i "s/{domain_name}/$DOMAIN_NAME/g" "$tmp_nginx_conf"
if ! cmp -s "$tmp_nginx_conf" "$dst_nginx_conf"; then
    install -m 644 "$tmp_nginx_conf" "$dst_nginx_conf"
    nginx -t
    systemctl reload nginx
fi
rm -f "$tmp_nginx_conf"

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

# Set proper permissions on media directory so that nginx can serve the files.
# Otherwise, we'll get 403 Forbidden errors.
MEDIA_DIR="/home/app-user/called/instance/media/"
mkdir -p "$MEDIA_DIR"
chown -R app-user:app-user "$MEDIA_DIR"
chmod -R 755 "$MEDIA_DIR"
for dir in /home/app-user{,/called{,/instance{,/media{,/missionaries{,/photos}}}}}; do
    chmod o+x "$dir"
done
