#!/bin/bash
# deploy.sh — run this ON your Hostinger VPS (SSH in first)
set -e

SITE_DIR="/var/www/valleyofthesunmoving"
NGINX_CONF="/etc/nginx/sites-available/valleyofthesunmoving"

echo "==> Installing nginx (if not already installed)..."
apt-get update -qq && apt-get install -y nginx

echo "==> Creating site directory..."
mkdir -p "$SITE_DIR"

echo "==> Copying site files..."
cp index.html "$SITE_DIR/"

echo "==> Installing nginx config..."
cp nginx.conf "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/valleyofthesunmoving
rm -f /etc/nginx/sites-enabled/default   # disable default page

echo "==> Testing nginx config..."
nginx -t

echo "==> Reloading nginx..."
systemctl reload nginx
systemctl enable nginx

echo ""
echo "Done! Your site is live at http://$(curl -s ifconfig.me)"
echo "Point your domain to this IP and update server_name in nginx.conf to go live on your domain."
