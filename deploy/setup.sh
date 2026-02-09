#!/bin/bash
# ============================================
# AI Character Chat — One-command VPS setup
# ============================================
# Usage:
#   git clone https://github.com/PSlava/ai-character-chat.git /opt/ai-chat
#   cd /opt/ai-chat
#   bash deploy/setup.sh
# ============================================
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

echo ""
echo "========================================"
echo "  AI Character Chat — VPS Setup"
echo "========================================"
echo ""

# ---- Step 1: Install Docker ----
if ! command -v docker &>/dev/null; then
    echo "[1/5] Installing Docker..."
    apt-get update -qq
    apt-get install -y -qq ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list
    apt-get update -qq
    apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
    systemctl enable docker
    echo "[1/5] Docker installed."
else
    echo "[1/5] Docker already installed, skipping."
fi

# ---- Step 2: Create .env ----
if [ ! -f "$REPO_DIR/.env" ]; then
    echo ""
    echo "[2/5] Configuring environment..."
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"

    # Generate random secrets
    JWT_SECRET=$(openssl rand -hex 32)
    PG_PASSWORD=$(openssl rand -hex 16)
    WH_SECRET=$(openssl rand -hex 16)

    sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$JWT_SECRET|" "$REPO_DIR/.env"
    sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$PG_PASSWORD|" "$REPO_DIR/.env"
    sed -i "s|^WEBHOOK_SECRET=.*|WEBHOOK_SECRET=$WH_SECRET|" "$REPO_DIR/.env"

    # Ask for domain
    echo ""
    read -rp "Domain name (or press Enter for IP-only): " DOMAIN
    if [ -n "$DOMAIN" ]; then
        sed -i "s|^DOMAIN=.*|DOMAIN=$DOMAIN|" "$REPO_DIR/.env"
    fi

    # Ask for API keys
    echo ""
    echo "Enter API keys (press Enter to skip):"
    echo ""

    read -rp "  GROQ_API_KEY: " KEY
    [ -n "$KEY" ] && sed -i "s|^GROQ_API_KEY=.*|GROQ_API_KEY=$KEY|" "$REPO_DIR/.env"

    read -rp "  CEREBRAS_API_KEY: " KEY
    [ -n "$KEY" ] && sed -i "s|^CEREBRAS_API_KEY=.*|CEREBRAS_API_KEY=$KEY|" "$REPO_DIR/.env"

    read -rp "  OPENROUTER_API_KEY: " KEY
    [ -n "$KEY" ] && sed -i "s|^OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=$KEY|" "$REPO_DIR/.env"

    read -rp "  DEEPSEEK_API_KEY: " KEY
    [ -n "$KEY" ] && sed -i "s|^DEEPSEEK_API_KEY=.*|DEEPSEEK_API_KEY=$KEY|" "$REPO_DIR/.env"

    read -rp "  QWEN_API_KEY: " KEY
    [ -n "$KEY" ] && sed -i "s|^QWEN_API_KEY=.*|QWEN_API_KEY=$KEY|" "$REPO_DIR/.env"

    echo ""
    echo "[2/5] Environment configured."
    echo "       Edit later: nano $REPO_DIR/.env"
else
    echo "[2/5] .env already exists, skipping."
fi

# ---- Step 3: Create cert directory ----
echo "[3/5] Preparing directories..."
mkdir -p "$REPO_DIR/deploy/nginx/certs"
chmod +x "$REPO_DIR/deploy/deploy.sh"

# ---- Step 4: Build and start ----
echo ""
echo "[4/5] Building and starting containers..."
cd "$REPO_DIR"
docker compose up -d --build

echo ""
echo "[4/5] Containers started. Waiting for health checks..."
sleep 10

# Check health
if curl -sf http://localhost/api/health > /dev/null 2>&1; then
    echo "       Backend: OK"
else
    echo "       Backend: starting up (may take a moment)..."
fi

# ---- Step 5: SSL (optional) ----
DOMAIN=$(grep "^DOMAIN=" "$REPO_DIR/.env" | cut -d= -f2)
if [ -n "$DOMAIN" ] && [ "$DOMAIN" != "chat.example.com" ]; then
    echo ""
    read -rp "[5/5] Set up HTTPS with Let's Encrypt for $DOMAIN? (y/N): " SSL
    if [ "$SSL" = "y" ] || [ "$SSL" = "Y" ]; then
        apt-get install -y -qq certbot
        certbot certonly --standalone --agree-tos --no-eff-email \
            -d "$DOMAIN" \
            --cert-name ai-chat
        # Copy certs
        cp /etc/letsencrypt/live/ai-chat/fullchain.pem "$REPO_DIR/deploy/nginx/certs/"
        cp /etc/letsencrypt/live/ai-chat/privkey.pem "$REPO_DIR/deploy/nginx/certs/"

        # Add certbot renewal cron
        echo "0 3 * * * certbot renew --quiet && cp /etc/letsencrypt/live/ai-chat/*.pem $REPO_DIR/deploy/nginx/certs/ && docker compose -f $REPO_DIR/docker-compose.yml restart nginx" \
            | crontab -

        echo "[5/5] HTTPS configured."
        echo "       Update deploy/nginx/nginx.conf to enable the HTTPS server block."
    else
        echo "[5/5] Skipping HTTPS."
    fi
else
    echo "[5/5] No domain configured, skipping HTTPS."
fi

# ---- Done ----
WH_SECRET=$(grep "^WEBHOOK_SECRET=" "$REPO_DIR/.env" | cut -d= -f2)
SERVER_IP=$(curl -sf ifconfig.me 2>/dev/null || echo "YOUR_IP")

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
echo "  App:     http://${DOMAIN:-$SERVER_IP}"
echo "  API:     http://${DOMAIN:-$SERVER_IP}/api/health"
echo "  Webhook: http://${SERVER_IP}:9000/webhook"
echo ""
echo "  GitHub Webhook setup:"
echo "    URL:    http://${SERVER_IP}:9000/webhook"
echo "    Secret: $WH_SECRET"
echo "    Events: Just the push event"
echo ""
echo "  Useful commands:"
echo "    docker compose logs -f          # View logs"
echo "    docker compose restart backend  # Restart backend"
echo "    bash deploy/deploy.sh           # Manual redeploy"
echo "    nano .env                       # Edit config"
echo ""
