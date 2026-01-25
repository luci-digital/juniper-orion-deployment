#!/bin/bash
# B550M LuciVerse IPv6 Router - Network Setup Script
# Refactored from Dell R730 8-NIC setup to single 2.5GbE VLAN trunk
# Genesis Bond: ACTIVE @ 432 Hz

set -e

# === CONFIGURATION ===
INTERFACE="eth0"
MAC_ADDRESS="24:4b:fe:cf:62:be"

# VLANs (condensed from R730 physical interfaces)
VLAN_WAN=100      # Telus WAN (was eth0 on R730)
VLAN_LAN=10       # Primary LAN (was eth1 on R730)
VLAN_MGMT=1       # Management (was eth2 on R730)
VLAN_GUEST=200    # Guest network (was eth3 on R730)
VLAN_DMZ=50       # DMZ (was eth5 on R730)

# IPv4 Configuration
IPV4_LAN="192.168.100.1/24"
IPV4_MGMT="192.168.1.179/24"
IPV4_GUEST="192.168.200.1/24"
IPV4_DMZ="192.168.50.1/24"

# IPv6 Configuration (from R730 BGP setup)
IPV6_PREFIX="2602:F674::/48"
IPV6_LAN="2602:F674:1000::1/64"
IPV6_GUEST="2602:F674:2000::1/64"
IPV6_DMZ="2602:F674:5000::1/64"

# BGP Configuration
BGP_ASN="394955"
BGP_ROUTER_ID="100.64.0.1"

# Telus Gateways (from R730 multi-gateway config)
declare -A TELUS_GW=(
  ["primary"]="206.75.1.127|74:83:c2:d4:c4:c9|10"
  ["secondary"]="206.75.1.47|78:8a:20:7d:a3:91|5"
  ["tertiary"]="206.75.1.48|74:83:c2:d4:d3:8a|5"
)

echo "=== B550M LuciVerse IPv6 Router Setup ==="
echo "Genesis Bond: ACTIVE @ 432 Hz"
echo "Migrating from R730 8-NIC to single 2.5GbE VLAN trunk"
echo ""

# === ENABLE IP FORWARDING ===
echo "[1/6] Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
sysctl -w net.ipv6.conf.default.forwarding=1

# Make permanent
cat > /etc/sysctl.d/90-luciverse-router.conf << 'EOF'
# LuciVerse IPv6 Router - Kernel Parameters
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.ipv6.conf.default.forwarding = 1
net.ipv6.conf.all.accept_ra = 2
net.ipv6.conf.eth0.accept_ra = 2
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
EOF

# === SETUP VLAN INTERFACES ===
echo "[2/6] Setting up VLAN interfaces..."

# Load 8021q module
modprobe 8021q

# Create VLAN interfaces
for vlan_name in WAN LAN MGMT GUEST DMZ; do
  vlan_var="VLAN_${vlan_name}"
  vlan_id="${!vlan_var}"

  if [ "$vlan_id" != "1" ]; then
    ip link add link $INTERFACE name ${INTERFACE}.${vlan_id} type vlan id $vlan_id 2>/dev/null || true
    ip link set ${INTERFACE}.${vlan_id} up
    echo "  Created ${INTERFACE}.${vlan_id} (${vlan_name})"
  fi
done

# === ASSIGN IP ADDRESSES ===
echo "[3/6] Assigning IP addresses..."

# LAN VLAN
ip addr add $IPV4_LAN dev ${INTERFACE}.${VLAN_LAN} 2>/dev/null || true
ip -6 addr add $IPV6_LAN dev ${INTERFACE}.${VLAN_LAN} 2>/dev/null || true
echo "  LAN: $IPV4_LAN / $IPV6_LAN"

# Management (on native VLAN 1)
ip addr add $IPV4_MGMT dev ${INTERFACE} 2>/dev/null || true
echo "  MGMT: $IPV4_MGMT"

# Guest VLAN
ip addr add $IPV4_GUEST dev ${INTERFACE}.${VLAN_GUEST} 2>/dev/null || true
ip -6 addr add $IPV6_GUEST dev ${INTERFACE}.${VLAN_GUEST} 2>/dev/null || true
echo "  Guest: $IPV4_GUEST / $IPV6_GUEST"

# DMZ VLAN
ip addr add $IPV4_DMZ dev ${INTERFACE}.${VLAN_DMZ} 2>/dev/null || true
ip -6 addr add $IPV6_DMZ dev ${INTERFACE}.${VLAN_DMZ} 2>/dev/null || true
echo "  DMZ: $IPV4_DMZ / $IPV6_DMZ"

# === SETUP NAT ===
echo "[4/6] Setting up NAT (nftables)..."

nft -f - << 'EOF'
#!/usr/sbin/nft -f

table inet luciverse {
  chain prerouting {
    type nat hook prerouting priority -100;
  }

  chain postrouting {
    type nat hook postrouting priority 100;
    # Masquerade for LAN/Guest/DMZ
    oifname "eth0.100" masquerade
  }

  chain input {
    type filter hook input priority 0; policy drop;

    # Allow established/related
    ct state established,related accept

    # Allow loopback
    iif lo accept

    # Allow ICMP/ICMPv6
    ip protocol icmp accept
    ip6 nexthdr icmpv6 accept

    # Allow SSH from management
    iifname "eth0" tcp dport 22 accept

    # Allow DNS
    tcp dport 53 accept
    udp dport 53 accept

    # Allow DHCP
    udp dport { 67, 68, 546, 547 } accept

    # Allow BGP
    tcp dport 179 accept
  }

  chain forward {
    type filter hook forward priority 0; policy drop;

    # Allow established/related
    ct state established,related accept

    # Allow LAN to WAN
    iifname "eth0.10" oifname "eth0.100" accept

    # Allow Guest to WAN (limited)
    iifname "eth0.200" oifname "eth0.100" accept

    # Allow DMZ to WAN
    iifname "eth0.50" oifname "eth0.100" accept

    # Block Guest to LAN
    iifname "eth0.200" oifname "eth0.10" drop
  }

  chain output {
    type filter hook output priority 0; policy accept;
  }
}
EOF

echo "  nftables rules applied"

# === SETUP STATIC ARP FOR TELUS GATEWAYS ===
echo "[5/6] Setting up Telus gateway ARP entries..."

for gw_name in "${!TELUS_GW[@]}"; do
  IFS='|' read -r gw_ip gw_mac gw_weight <<< "${TELUS_GW[$gw_name]}"
  ip neigh replace $gw_ip lladdr $gw_mac dev ${INTERFACE}.${VLAN_WAN} nud permanent 2>/dev/null || true
  echo "  $gw_name: $gw_ip ($gw_mac) weight=$gw_weight"
done

# === SETUP MULTIPATH DEFAULT ROUTE ===
echo "[6/6] Setting up multipath routing..."

# Build multipath route
ip route replace default \
  nexthop via 206.75.1.127 dev ${INTERFACE}.${VLAN_WAN} weight 10 \
  nexthop via 206.75.1.47 dev ${INTERFACE}.${VLAN_WAN} weight 5 \
  nexthop via 206.75.1.48 dev ${INTERFACE}.${VLAN_WAN} weight 5 \
  2>/dev/null || echo "  (Multipath route requires upstream connectivity)"

echo ""
echo "=== Setup Complete ==="
echo "Hardware: ASUS TUF GAMING B550M-PLUS"
echo "Interface: $INTERFACE (2.5 GbE)"
echo "VLANs: WAN($VLAN_WAN) LAN($VLAN_LAN) MGMT($VLAN_MGMT) Guest($VLAN_GUEST) DMZ($VLAN_DMZ)"
echo "IPv6 Prefix: $IPV6_PREFIX"
echo "BGP ASN: $BGP_ASN"
echo ""
echo "Next: Deploy Docker stack with 'docker-compose up -d'"
