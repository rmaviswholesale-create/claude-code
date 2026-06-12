#!/bin/bash
# Valley of the Sun Moving LLC - VPS Deploy Script
# Run ON your Hostinger VPS: ssh root@VPS_IP then bash deploy.sh
set -e
SITE_DIR="/var/www/valleyofthesunmoving"
NGINX_CONF="/etc/nginx/sites-available/valleyofthesunmoving"
if ! command -v nginx &>/dev/null; then
  apt-get update -qq && apt-get install -y nginx
fi
mkdir -p "$SITE_DIR"
cp index.html "$SITE_DIR/"
chmod 644 "$SITE_DIR/index.html"
chown -R www-data:www-data "$SITE_DIR"
cp nginx.conf "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/valleyofthesunmoving
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl enable nginx && systemctl reload nginx
echo "Site live at: http://$(curl -s ifconfig.me)"
