#!/bin/bash
# ============================================================
# Valley of the Sun Moving LLC — VPS Deploy Script
# Run this ON your Hostinger VPS after SSH-ing in.
#
# Usage:
#   1. SSH into your VPS:  ssh root@YOUR_VPS_IP
#   2. Upload files first:
#        scp index.html nginx.conf deploy.sh root@YOUR_VPS_IP:~/
#   3. Run:  bash deploy.sh
# ============================================================
set -e

SITE_DIR="/var/www/valleyofthesunmoving"
NGINX_CONF="/etc/nginx/sites-available/valleyofthesunmoving"
NGINX_LINK="/etc/nginx/sites-enabled/valleyofthesunmoving"

echo ""
echo "===== Valley of the Sun Moving — Deploying Site ====="
echo ""

# Install nginx if missing
if ! command -v nginx &>/dev/null; then
  echo "--> Installing nginx..."
  apt-get update -qq
  apt-get install -y nginx
else
  echo "--> nginx already installed."
fi

# Create and populate site directory
echo "--> Deploying site files to $SITE_DIR..."
mkdir -p "$SITE_DIR"
cp index.html "$SITE_DIR/index.html"
chmod 644 "$SITE_DIR/index.html"
chown -R www-data:www-data "$SITE_DIR"

# Install nginx config
echo "--> Installing nginx config..."
cp nginx.conf "$NGINX_CONF"
ln -sf "$NGINX_CONF" "$NGINX_LINK"
rm -f /etc/nginx/sites-enabled/default   # remove default "Welcome to nginx" page

# Test and reload
echo "--> Testing nginx config..."
nginx -t

echo "--> Enabling and reloading nginx..."
systemctl enable nginx
systemctl reload nginx

# Report public IP
PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || echo "unknown")
echo ""
echo "====================================================="
echo "  Site is LIVE at: http://$PUBLIC_IP"
echo ""
echo "  Next steps:"
echo "  1. Update phone/email placeholders in index.html"
echo "  2. Point your domain's DNS A record to: $PUBLIC_IP"
echo "  3. Update 'server_name' in nginx.conf with your domain"
echo "  4. (Optional) Add SSL: apt install certbot python3-certbot-nginx"
echo "         then: certbot --nginx -d yourdomain.com -d www.yourdomain.com"
echo "====================================================="
