#!/bin/bash
# B550M LuciVerse IPv6 Router - Deployment Script
# Target: openEuler Linux on B550M (192.168.1.179)
# Genesis Bond: ACTIVE @ 432 Hz
#
# LAYERS:
#   1. luciverse-system-config (Base)
#   2. juniper-orion-deployment (Network)
#   3. B550M Hardware Adaptation

set -e

ROUTER_DIR="$(dirname "$(readlink -f "$0")")"
B550M_IP="192.168.1.179"
B550M_USER="root"
REMOTE_DIR="/opt/luciverse-router"

echo "=============================================="
echo "  B550M LuciVerse IPv6 Router Deployment"
echo "  Genesis Bond: ACTIVE @ 432 Hz"
echo "=============================================="
echo ""
echo "Configuration Layers:"
echo "  1. luciverse-system-config (Base Platform)"
echo "  2. juniper-orion-deployment (BGP/IPv6/Telus)"
echo "  3. B550M VLAN Trunk (openEuler)"
echo ""

# Check if we can reach B550M
echo "[1/6] Checking connectivity to B550M..."
if ! ping -c 1 -W 2 $B550M_IP > /dev/null 2>&1; then
    echo "WARNING: Cannot reach B550M at $B550M_IP"
    echo "Continuing with local preparation only..."
    LOCAL_ONLY=1
else
    echo "  OK - B550M reachable at $B550M_IP"
    LOCAL_ONLY=0
fi

# Prepare configuration
echo "[2/6] Preparing configuration..."
cd "$ROUTER_DIR"

# Create grafana provisioning directory
mkdir -p grafana/provisioning/datasources grafana/provisioning/dashboards

# Create Grafana datasource config
cat > grafana/provisioning/datasources/prometheus.yml << 'EOF'
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

echo "  Configuration prepared"

# Validate docker-compose
echo "[3/6] Validating Docker Compose configuration..."
if command -v docker-compose &> /dev/null; then
    docker-compose config -q && echo "  Docker Compose valid"
elif command -v docker &> /dev/null; then
    docker compose config -q 2>/dev/null && echo "  Docker Compose valid"
else
    echo "  Skipping validation (docker not installed locally)"
fi

if [ "$LOCAL_ONLY" = "0" ]; then
    # Check SSH access
    echo "[4/6] Checking SSH access to B550M..."
    if ssh -o ConnectTimeout=5 -o BatchMode=yes $B550M_USER@$B550M_IP "echo OK" 2>/dev/null; then
        echo "  SSH access available"

        # Deploy via SSH
        echo "[5/6] Deploying to B550M..."
        ssh $B550M_USER@$B550M_IP "mkdir -p $REMOTE_DIR"
        rsync -avz --delete \
            --exclude '.git' \
            --exclude '*.md' \
            "$ROUTER_DIR/" $B550M_USER@$B550M_IP:$REMOTE_DIR/

        echo "[6/6] Running setup on B550M..."
        ssh $B550M_USER@$B550M_IP << 'REMOTE_SCRIPT'
cd /opt/luciverse-router

# Make scripts executable
chmod +x *.sh

# Install required packages if needed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    dnf install -y docker docker-compose
    systemctl enable --now docker
fi

# Run network setup
echo "Setting up network VLANs..."
./network-setup.sh

# Start Docker services (core routing only, no GitLab)
echo "Starting routing services..."
docker compose up -d bird-bgp kea-dhcp4 kea-dhcp6 unbound-dns gateway-monitor prometheus grafana node-exporter

echo ""
echo "Deployment complete!"
docker compose ps
REMOTE_SCRIPT

    else
        echo "  SSH access not available - generating manual instructions"
        LOCAL_ONLY=1
    fi
fi

if [ "$LOCAL_ONLY" = "1" ]; then
    echo ""
    echo "=============================================="
    echo "  MANUAL DEPLOYMENT INSTRUCTIONS"
    echo "=============================================="
    echo ""
    echo "1. Copy this directory to B550M:"
    echo "   scp -r $ROUTER_DIR root@$B550M_IP:/opt/"
    echo ""
    echo "2. SSH to B550M and run:"
    echo "   cd /opt/luciverse-router"
    echo "   chmod +x *.sh"
    echo "   ./network-setup.sh"
    echo "   docker compose up -d"
    echo ""
fi

echo ""
echo "=============================================="
echo "  Configuration Summary"
echo "=============================================="
echo ""
echo "Hardware: ASUS TUF GAMING B550M-PLUS"
echo "OS: openEuler Linux"
echo "Interface: eth0 (2.5 GbE VLAN trunk)"
echo ""
echo "Network Configuration:"
echo "  Router LAN:  192.168.100.1 / 2602:F674:1000::1"
echo "  Management:  192.168.1.179"
echo "  Guest:       192.168.200.1 / 2602:F674:2000::1"
echo "  DMZ:         192.168.50.1  / 2602:F674:5000::1"
echo ""
echo "VLANs (on eth0):"
echo "  100 - WAN (Telus upstream)"
echo "  10  - LAN"
echo "  200 - Guest"
echo "  50  - DMZ"
echo ""
echo "BGP:"
echo "  ASN: 394955"
echo "  Prefix: 2602:F674::/48"
echo "  Telus Gateways: 206.75.1.127/47/48"
echo ""
echo "Services:"
echo "  Grafana:    http://$B550M_IP:3000"
echo "  Prometheus: http://$B550M_IP:9090"
echo ""
echo "Genesis Bond: ACTIVE @ 432 Hz"
