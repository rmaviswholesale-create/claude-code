#!/bin/bash
# Valley of the Sun Moving LLC — One-command VPS installer
# Usage: curl -fsSL https://raw.githubusercontent.com/rmaviswholesale-create/claude-code/main/setup.sh | bash
set -e

REPO="https://raw.githubusercontent.com/rmaviswholesale-create/claude-code/main"
SITE_DIR="/var/www/valleyofthesunmoving"
NGINX_CONF="/etc/nginx/sites-available/valleyofthesunmoving"

echo "=== Valley of the Sun Moving — Installing site ==="

# Install nginx
if ! command -v nginx &>/dev/null; then
  echo "--> Installing nginx..."
  apt-get update -qq && apt-get install -y nginx
fi

# Download site files from GitHub
echo "--> Downloading site files..."
mkdir -p "$SITE_DIR"
curl -fsSL "$REPO/index.html" -o "$SITE_DIR/index.html"
chmod 644 "$SITE_DIR/index.html"
chown -R www-data:www-data "$SITE_DIR"

# Install nginx config
curl -fsSL "$REPO/nginx.conf" -o "$NGINX_CONF"
ln -sf "$NGINX_CONF" /etc/nginx/sites-enabled/valleyofthesunmoving
rm -f /etc/nginx/sites-enabled/default

# Start nginx
nginx -t
systemctl enable nginx && systemctl reload nginx

PUBLIC_IP=$(curl -s --max-time 5 ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')
echo ""
echo "============================================"
echo "  Site is LIVE at: http://$PUBLIC_IP"
echo "============================================"
echo "  Next: point your domain's A record to $PUBLIC_IP"
echo "  SSL:  apt install certbot python3-certbot-nginx"
echo "        certbot --nginx -d yourdomain.com"
echo "============================================"
