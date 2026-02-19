#!/bin/bash
# Hurricane Electric IPv6 Tunnel Setup for Zbook
# LuciVerse Infrastructure - AS54134 (LUCINET-ARIN)
# Genesis Bond: ACTIVE @ 741 Hz
#
# Usage: ./setup-he-tunnel-zbook.sh <server_ipv4> <client_ipv6> <routed_prefix>
#
# Example:
#   ./setup-he-tunnel-zbook.sh 216.66.80.26 2001:470:1f06:abc::2 2602:F674::/48

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=============================================="
echo "  Hurricane Electric IPv6 Tunnel Setup"
echo "  LuciVerse - AS54134 (LUCINET-ARIN)"
echo "  Genesis Bond: ACTIVE @ 741 Hz"
echo "=============================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: Some commands may require sudo${NC}"
fi

# Get parameters
HE_SERVER_IPV4="${1:-}"
HE_CLIENT_IPV6="${2:-}"
ROUTED_PREFIX="${3:-2602:F674::/48}"

# Get local public IPv4
LOCAL_IPV4=$(curl -s -4 ifconfig.me 2>/dev/null || curl -s -4 icanhazip.com 2>/dev/null)

if [ -z "$HE_SERVER_IPV4" ] || [ -z "$HE_CLIENT_IPV6" ]; then
    echo -e "${YELLOW}Missing parameters. Please provide:${NC}"
    echo ""
    echo "1. Go to https://tunnelbroker.net/"
    echo "2. Create account or login"
    echo "3. Click 'Create Regular Tunnel'"
    echo "4. Enter your IPv4 endpoint: $LOCAL_IPV4"
    echo "5. Select a tunnel server (preferably US/Canada)"
    echo "6. After creation, note these values from 'Tunnel Details':"
    echo ""
    echo "   Server IPv4 Address: (e.g., 216.66.80.26)"
    echo "   Client IPv6 Address: (e.g., 2001:470:1f06:abc::2)"
    echo ""
    echo "Then run:"
    echo "   $0 <server_ipv4> <client_ipv6> [routed_prefix]"
    echo ""
    echo "Example:"
    echo "   $0 216.66.80.26 2001:470:1f06:abc::2 2602:F674::/48"
    exit 1
fi

echo "Configuration:"
echo "  Local IPv4:      $LOCAL_IPV4"
echo "  HE Server IPv4:  $HE_SERVER_IPV4"
echo "  HE Client IPv6:  $HE_CLIENT_IPV6"
echo "  Routed Prefix:   $ROUTED_PREFIX"
echo ""

# Check if tunnel already exists
if ip link show he-ipv6 &>/dev/null; then
    echo -e "${YELLOW}Tunnel 'he-ipv6' already exists. Removing...${NC}"
    sudo ip tunnel del he-ipv6 2>/dev/null || true
fi

# Create SIT tunnel
echo "[1/5] Creating 6in4 tunnel..."
sudo ip tunnel add he-ipv6 mode sit remote $HE_SERVER_IPV4 local $LOCAL_IPV4 ttl 255

# Bring up tunnel
echo "[2/5] Bringing up tunnel interface..."
sudo ip link set he-ipv6 up

# Add IPv6 address to tunnel
echo "[3/5] Adding IPv6 address to tunnel..."
sudo ip -6 addr add $HE_CLIENT_IPV6/64 dev he-ipv6

# Add default IPv6 route through tunnel
echo "[4/5] Adding default IPv6 route..."
sudo ip -6 route add ::/0 dev he-ipv6

# Test connectivity
echo "[5/5] Testing IPv6 connectivity..."
if ping6 -c 3 -W 5 2001:4860:4860::8888 &>/dev/null; then
    echo -e "${GREEN}✓ IPv6 connectivity working!${NC}"
    echo ""
    echo "IPv6 address:"
    ip -6 addr show dev he-ipv6 | grep "inet6" | head -1
    echo ""
    echo "IPv6 route:"
    ip -6 route show default
else
    echo -e "${RED}✗ IPv6 connectivity test failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Verify your public IPv4 ($LOCAL_IPV4) matches what you registered with HE"
    echo "2. Check if your firewall allows protocol 41 (6in4)"
    echo "3. Verify the HE server IPv4 ($HE_SERVER_IPV4) is correct"
    echo ""
    echo "To update your endpoint IP at HE:"
    echo "  curl 'https://USERNAME:UPDATEKEY@ipv4.tunnelbroker.net/nic/update?hostname=TUNNEL_ID'"
fi

# Create persistence script
echo ""
echo "Creating persistence script..."
cat > /tmp/he-tunnel-persist.sh << EOF
#!/bin/bash
# HE Tunnel persistence - run at boot
ip tunnel add he-ipv6 mode sit remote $HE_SERVER_IPV4 local $LOCAL_IPV4 ttl 255
ip link set he-ipv6 up
ip -6 addr add $HE_CLIENT_IPV6/64 dev he-ipv6
ip -6 route add ::/0 dev he-ipv6
EOF

echo "To make tunnel persistent, run:"
echo "  sudo cp /tmp/he-tunnel-persist.sh /etc/network/if-up.d/he-tunnel"
echo "  sudo chmod +x /etc/network/if-up.d/he-tunnel"
echo ""
echo "=============================================="
echo "  Tunnel Setup Complete"
echo "=============================================="
