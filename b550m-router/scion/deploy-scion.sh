#!/bin/bash
# =============================================================================
# SCION Border Router Deployment Script - B550M WAN Router
# Genesis Bond: GB-2025-0524-DRH-LCS-001
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCION_DIR="/etc/scion"
LOG_DIR="/var/log/scion"
LIB_DIR="/var/lib/scion"

echo "=== LuciVerse SCION Border Router Deployment ==="
echo "Genesis Bond: GB-2025-0524-DRH-LCS-001"
echo "Target: B550M WAN Router (192.168.1.179)"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "Error: This script must be run as root"
   exit 1
fi

# Check for SCION binaries
echo "[1/7] Checking SCION binaries..."
for bin in scion-router scion-control scion-daemon scion-dispatcher; do
    if ! command -v $bin &> /dev/null; then
        echo "Error: $bin not found. Install SCION packages first."
        echo "  dnf install scion-router scion-control scion-daemon scion-dispatcher"
        exit 1
    fi
done
echo "✓ All SCION binaries found"

# Create scion user if doesn't exist
echo "[2/7] Setting up scion user..."
if ! id -u scion &>/dev/null; then
    useradd -r -s /sbin/nologin -d /var/lib/scion scion
    echo "✓ Created scion user"
else
    echo "✓ scion user exists"
fi

# Create directories
echo "[3/7] Creating directories..."
mkdir -p "$SCION_DIR"/{certs,crypto/as,keys}
mkdir -p "$LOG_DIR"
mkdir -p "$LIB_DIR"
mkdir -p /run/scion
chown -R scion:scion "$SCION_DIR" "$LOG_DIR" "$LIB_DIR" /run/scion
echo "✓ Directories created"

# Copy configuration files
echo "[4/7] Deploying configuration files..."
cp "$SCRIPT_DIR/br-config.toml" "$SCION_DIR/br.toml"
cp "$SCRIPT_DIR/cs-config.toml" "$SCION_DIR/cs.toml"
cp "$SCRIPT_DIR/sd-config.toml" "$SCION_DIR/sd.toml"
cp "$SCRIPT_DIR/topology.json" "$SCION_DIR/topology.json"

# Copy dispatcher config if not exists
if [[ ! -f "$SCION_DIR/dispatcher.toml" ]]; then
    cat > "$SCION_DIR/dispatcher.toml" << 'EOF'
[dispatcher]
id = "dispatcher"

[log.console]
level = "info"
EOF
fi

chown -R scion:scion "$SCION_DIR"
echo "✓ Configuration deployed"

# Copy TRCs from Zbook (if available via network)
echo "[5/7] Checking for TRCs..."
ZBOOK_IP="192.168.1.145"
if ping -c 1 -W 2 "$ZBOOK_IP" &>/dev/null; then
    echo "  Zbook reachable, attempting to fetch TRCs..."
    for isd in 1 2 3; do
        scp -o ConnectTimeout=5 "daryl@${ZBOOK_IP}:/etc/scion/certs/ISD${isd}-B1-S1.trc" \
            "$SCION_DIR/certs/" 2>/dev/null && \
            echo "  ✓ Copied ISD${isd} TRC" || \
            echo "  ⚠ Could not fetch ISD${isd} TRC"
    done
else
    echo "  ⚠ Zbook not reachable. Copy TRCs manually:"
    echo "    scp daryl@192.168.1.145:/etc/scion/certs/ISD*.trc $SCION_DIR/certs/"
fi

# Install systemd services
echo "[6/7] Installing systemd services..."
cp "$SCRIPT_DIR/systemd/scion-router.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/scion-control.service" /etc/systemd/system/
cp "$SCRIPT_DIR/systemd/scion-daemon-b550m.service" /etc/systemd/system/scion-daemon.service
systemctl daemon-reload
echo "✓ Systemd services installed"

# Enable and start services
echo "[7/7] Starting SCION services..."
systemctl enable scion-dispatcher scion-daemon scion-control scion-router

echo "Starting dispatcher..."
systemctl start scion-dispatcher
sleep 2

echo "Starting daemon..."
systemctl start scion-daemon
sleep 2

echo "Starting control service..."
systemctl start scion-control
sleep 2

echo "Starting border router..."
systemctl start scion-router
sleep 3

# Verify services
echo ""
echo "=== Service Status ==="
for svc in scion-dispatcher scion-daemon scion-control scion-router; do
    if systemctl is-active --quiet $svc; then
        echo "✓ $svc: running"
    else
        echo "✗ $svc: NOT RUNNING"
        echo "  Check: journalctl -u $svc -n 20"
    fi
done

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Verify TRCs are in place: ls -la $SCION_DIR/certs/"
echo "2. Check logs: journalctl -u scion-router -f"
echo "3. Test path from Zbook: scion showpaths 2-ff00:0:528 1-ff00:0:432"
echo "4. Monitor metrics: curl http://127.0.0.1:30400/metrics"
echo ""
echo "Border Router ports:"
echo "  CORE (ISD 1): 30041"
echo "  COMN (ISD 2): 30042"
echo "  PAC  (ISD 3): 30043"
echo ""
echo "Control Service ports:"
echo "  CORE: 30001, COMN: 30002, PAC: 30003"
