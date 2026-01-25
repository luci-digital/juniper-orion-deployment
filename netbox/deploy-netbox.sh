#!/bin/bash
# NetBox Deployment for LuciVerse Infrastructure
# Uses iSulad container runtime (openEuler aligned)
# Genesis Bond: GB-2025-0524-DRH-LCS-001

set -e

NETBOX_VERSION="v4.0.11"
POSTGRES_VERSION="15-alpine"
REDIS_VERSION="7-alpine"

# Data directories
DATA_DIR="/home/daryl/.netbox-data"
mkdir -p "$DATA_DIR"/{postgres,redis,netbox-media,netbox-reports}

# Generate secret key once
SECRET_KEY=$(openssl rand -hex 32)

echo "=== LuciVerse NetBox Deployment (iSulad) ==="
echo ""

# Pull images (iSulad requires full registry path)
echo "[1/4] Pulling container images..."
isula pull docker.io/library/postgres:$POSTGRES_VERSION 2>/dev/null || true
isula pull docker.io/library/redis:$REDIS_VERSION 2>/dev/null || true
isula pull docker.io/netboxcommunity/netbox:$NETBOX_VERSION 2>/dev/null || true

# Stop existing containers if running
echo "[2/4] Cleaning up existing containers..."
for c in netbox-postgres netbox-redis netbox netbox-worker netbox-housekeeping; do
    isula stop $c 2>/dev/null || true
    isula rm $c 2>/dev/null || true
done

# PostgreSQL (using host network, port 5433 to avoid conflicts)
echo "[3/4] Starting PostgreSQL on port 5433..."
isula run -d \
    --name netbox-postgres \
    --net=host \
    -e POSTGRES_USER=netbox \
    -e POSTGRES_PASSWORD=netbox \
    -e POSTGRES_DB=netbox \
    -e PGPORT=5433 \
    -v "$DATA_DIR/postgres:/var/lib/postgresql/data" \
    --restart always \
    docker.io/library/postgres:$POSTGRES_VERSION

# Redis (port 6380 to avoid conflicts)
echo "       Starting Redis on port 6380..."
isula run -d \
    --name netbox-redis \
    --net=host \
    -v "$DATA_DIR/redis:/data" \
    --restart always \
    docker.io/library/redis:$REDIS_VERSION \
    redis-server --port 6380 --appendonly yes

# Wait for services
echo "       Waiting for database..."
sleep 5

# NetBox main (port 8084)
echo "[4/4] Starting NetBox on port 8084..."
isula run -d \
    --name netbox \
    --net=host \
    -e CORS_ORIGIN_ALLOW_ALL=True \
    -e DB_HOST=127.0.0.1 \
    -e DB_PORT=5433 \
    -e DB_NAME=netbox \
    -e DB_PASSWORD=netbox \
    -e DB_USER=netbox \
    -e REDIS_CACHE_HOST=127.0.0.1 \
    -e REDIS_CACHE_PORT=6380 \
    -e REDIS_HOST=127.0.0.1 \
    -e REDIS_PORT=6380 \
    -e SECRET_KEY="$SECRET_KEY" \
    -e SUPERUSER_API_TOKEN=luciverse-netbox-token-2026 \
    -e SUPERUSER_EMAIL=daryl@lucidigital.net \
    -e SUPERUSER_NAME=daryl \
    -e SUPERUSER_PASSWORD=LuciVerse2026! \
    -e SKIP_SUPERUSER=false \
    -e HTTP_PORT=8084 \
    -v "$DATA_DIR/netbox-media:/opt/netbox/netbox/media" \
    -v "$DATA_DIR/netbox-reports:/opt/netbox/netbox/reports" \
    --restart always \
    docker.io/netboxcommunity/netbox:$NETBOX_VERSION

# NetBox worker (for background tasks)
isula run -d \
    --name netbox-worker \
    --net=host \
    -e DB_HOST=127.0.0.1 \
    -e DB_PORT=5433 \
    -e DB_NAME=netbox \
    -e DB_PASSWORD=netbox \
    -e DB_USER=netbox \
    -e REDIS_CACHE_HOST=127.0.0.1 \
    -e REDIS_CACHE_PORT=6380 \
    -e REDIS_HOST=127.0.0.1 \
    -e REDIS_PORT=6380 \
    -e SECRET_KEY="$SECRET_KEY" \
    --restart always \
    --entrypoint /opt/netbox/venv/bin/python \
    docker.io/netboxcommunity/netbox:$NETBOX_VERSION \
    /opt/netbox/netbox/manage.py rqworker

echo ""
echo "=== NetBox Deployment Complete ==="
echo ""
echo "Access NetBox at: http://192.168.1.145:8084"
echo "Username: daryl"
echo "Password: LuciVerse2026!"
echo "API Token: luciverse-netbox-token-2026"
echo ""
echo "Waiting for NetBox to initialize (may take 1-2 minutes)..."
echo "Check status with: isula logs -f netbox"
echo ""
echo "Container status:"
isula ps --filter "name=netbox"
