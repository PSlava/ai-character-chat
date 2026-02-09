#!/bin/bash
# ============================================
# AI Character Chat — One-command VPS setup
# ============================================
#
# First install (interactive):
#   git clone https://github.com/PSlava/ai-character-chat.git /opt/ai-chat
#   cd /opt/ai-chat
#   bash deploy/setup.sh
#
# First install (non-interactive, pre-filled .env):
#   cp .env.example .env && nano .env
#   bash deploy/setup.sh --auto
#
# Re-run after adding domain:
#   nano .env                    # set DOMAIN=mysite.com
#   bash deploy/setup.sh         # will detect domain and offer SSL
#
# Change config without full rebuild:
#   nano .env
#   docker compose up -d
#
# ============================================
set -e

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR"

# Parse flags
AUTO_MODE=false
for arg in "$@"; do
    case "$arg" in
        --auto|--non-interactive|--no-interactive|-y)
            AUTO_MODE=true
            ;;
    esac
done

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

# ---- Step 2: Configure .env ----
echo ""

# Helper: generate secret if value is empty or placeholder
ensure_secret() {
    local KEY="$1"
    local CURRENT
    CURRENT=$(grep "^${KEY}=" "$REPO_DIR/.env" | cut -d= -f2-)
    if [ -z "$CURRENT" ] || [ "$CURRENT" = "change-me-to-random-string" ] || [ "$CURRENT" = "change-me-to-another-random-string" ] || [ "$CURRENT" = "change-me-to-webhook-secret" ]; then
        local SECRET
        SECRET=$(openssl rand -hex 32)
        sed -i "s|^${KEY}=.*|${KEY}=${SECRET}|" "$REPO_DIR/.env"
        echo "       Generated $KEY"
    fi
}

if [ ! -f "$REPO_DIR/.env" ]; then
    echo "[2/5] Creating .env from .env.example..."
    cp "$REPO_DIR/.env.example" "$REPO_DIR/.env"

    # Generate secrets
    ensure_secret "JWT_SECRET"
    ensure_secret "POSTGRES_PASSWORD"
    ensure_secret "WEBHOOK_SECRET"

    if [ "$AUTO_MODE" = true ]; then
        echo "[2/5] Auto mode: using .env as-is (edit later with: nano .env)"
    else
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
    fi
else
    echo "[2/5] Using existing .env file."
    # Ensure secrets are generated (in case user left placeholders)
    ensure_secret "JWT_SECRET"
    ensure_secret "POSTGRES_PASSWORD"
    ensure_secret "WEBHOOK_SECRET"
fi

# Show active API keys
echo ""
echo "       Active API keys:"
for KEY_NAME in GROQ_API_KEY CEREBRAS_API_KEY OPENROUTER_API_KEY DEEPSEEK_API_KEY QWEN_API_KEY ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY; do
    VAL=$(grep "^${KEY_NAME}=" "$REPO_DIR/.env" | cut -d= -f2-)
    if [ -n "$VAL" ]; then
        echo "         $KEY_NAME: ${VAL:0:8}..."
    fi
done
echo ""

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
CERTS_DIR="$REPO_DIR/deploy/nginx/certs"
HAS_CERT=false
if [ -f "$CERTS_DIR/fullchain.pem" ] && [ -f "$CERTS_DIR/privkey.pem" ]; then
    HAS_CERT=true
fi

if [ -n "$DOMAIN" ]; then
    if [ "$HAS_CERT" = true ]; then
        echo "[5/5] SSL certificate already exists for $DOMAIN."
        echo "       HTTPS is active."
    elif [ "$AUTO_MODE" = true ]; then
        echo "[5/5] Domain: $DOMAIN. To set up HTTPS, re-run without --auto:"
        echo "       bash deploy/setup.sh"
    else
        echo ""
        read -rp "[5/5] Set up HTTPS with Let's Encrypt for $DOMAIN? (y/N): " SSL
        if [ "$SSL" = "y" ] || [ "$SSL" = "Y" ]; then
            # Install certbot
            if ! command -v certbot &>/dev/null; then
                apt-get install -y -qq certbot
            fi

            # Stop nginx to free port 80 for certbot
            echo "       Stopping nginx for certificate request..."
            docker compose stop nginx

            # Get certificate
            certbot certonly --standalone --agree-tos --no-eff-email \
                -d "$DOMAIN" \
                --cert-name ai-chat

            # Copy certs
            cp /etc/letsencrypt/live/ai-chat/fullchain.pem "$CERTS_DIR/"
            cp /etc/letsencrypt/live/ai-chat/privkey.pem "$CERTS_DIR/"

            # Generate HTTPS nginx config
            sed "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" \
                "$REPO_DIR/deploy/nginx/nginx-ssl.conf" \
                > "$REPO_DIR/deploy/nginx/nginx.conf"

            # Restart nginx with new config
            docker compose up -d nginx
            echo "       HTTPS configured and nginx restarted."

            # Add certbot renewal cron
            CRON_CMD="0 3 * * * certbot renew --quiet --deploy-hook 'cp /etc/letsencrypt/live/ai-chat/*.pem $CERTS_DIR/ && docker compose -f $REPO_DIR/docker-compose.yml restart nginx'"
            # Check if cron already exists
            if ! crontab -l 2>/dev/null | grep -q "certbot renew"; then
                (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
                echo "       Certbot auto-renewal cron added."
            fi

            echo "[5/5] HTTPS enabled for $DOMAIN."
        else
            echo "[5/5] Skipping HTTPS."
        fi
    fi
else
    echo "[5/5] No domain configured, skipping HTTPS."
    echo "       To add later: set DOMAIN in .env, then re-run setup.sh"
fi

# ---- Done ----
WH_SECRET=$(grep "^WEBHOOK_SECRET=" "$REPO_DIR/.env" | cut -d= -f2)
SERVER_IP=$(curl -sf ifconfig.me 2>/dev/null || echo "YOUR_IP")

echo ""
echo "========================================"
echo "  Setup complete!"
echo "========================================"
echo ""
if [ -n "$DOMAIN" ] && [ "$HAS_CERT" = true -o -f "$CERTS_DIR/fullchain.pem" ]; then
    echo "  App:     https://$DOMAIN"
    echo "  API:     https://$DOMAIN/api/health"
else
    echo "  App:     http://${DOMAIN:-$SERVER_IP}"
    echo "  API:     http://${DOMAIN:-$SERVER_IP}/api/health"
fi
echo "  Webhook: http://${SERVER_IP}:9000/webhook"
echo ""
echo "  GitHub Webhook setup:"
echo "    URL:    http://${SERVER_IP}:9000/webhook"
echo "    Secret: $WH_SECRET"
echo "    Events: Just the push event"
echo ""
echo "  To change configuration:"
echo "    nano .env                            # edit settings"
echo "    docker compose up -d                 # apply changes"
echo ""
if [ -z "$DOMAIN" ]; then
    echo "  To add domain + HTTPS later:"
    echo "    nano .env                            # set DOMAIN=mysite.com"
    echo "    bash deploy/setup.sh                 # will set up SSL"
    echo ""
fi
echo "  Other commands:"
echo "    docker compose logs -f               # view logs"
echo "    docker compose restart backend       # restart backend"
echo "    docker compose up -d --build         # full rebuild"
echo "    bash deploy/deploy.sh                # pull + rebuild"
echo ""
