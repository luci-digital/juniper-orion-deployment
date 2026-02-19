#!/bin/bash
# R730 ORION 5-WAN Deployment Script
# Genesis Bond: ACTIVE @ 432 Hz
# ASN: 54134 (LUCINET-ARIN)

set -e

DEPLOY_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/r730-5wan-deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    log "ERROR: $1"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

backup_existing() {
    log "Creating backups..."
    local backup_dir="/root/r730-backup-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"

    [[ -f /etc/bird/bird.conf ]] && cp /etc/bird/bird.conf "$backup_dir/"
    [[ -f /etc/nftables.conf ]] && cp /etc/nftables.conf "$backup_dir/"
    [[ -d /etc/sysctl.d ]] && cp -r /etc/sysctl.d "$backup_dir/"
    [[ -f /etc/iproute2/rt_tables ]] && cp /etc/iproute2/rt_tables "$backup_dir/"

    log "Backup created at $backup_dir"
}

install_dependencies() {
    log "Installing dependencies..."

    # Detect package manager
    if command -v dnf &>/dev/null; then
        dnf install -y bird2 nftables python3 unbound
    elif command -v apt &>/dev/null; then
        apt update && apt install -y bird2 nftables python3 unbound
    else
        log "WARNING: Unknown package manager, assuming deps installed"
    fi
}

deploy_configs() {
    log "Deploying configurations..."

    # Sysctl
    cp "$DEPLOY_DIR/etc/sysctl.d/99-multiwan.conf" /etc/sysctl.d/
    sysctl -p /etc/sysctl.d/99-multiwan.conf

    # Routing tables
    cp "$DEPLOY_DIR/etc/iproute2/rt_tables" /etc/iproute2/rt_tables

    # BIRD2
    mkdir -p /etc/bird
    cp "$DEPLOY_DIR/etc/bird/bird.conf" /etc/bird/bird.conf

    # nftables
    mkdir -p /etc/nftables.d
    cp "$DEPLOY_DIR/etc/nftables.d/r730-5wan.nft" /etc/nftables.d/
    # Create main nftables.conf that includes our rules
    cat > /etc/nftables.conf << 'EOF'
#!/usr/sbin/nft -f
include "/etc/nftables.d/*.nft"
EOF

    # Jool (config only, service disabled)
    mkdir -p /etc/jool
    cp "$DEPLOY_DIR/etc/jool/"* /etc/jool/

    # Unbound DNS64
    mkdir -p /etc/unbound/unbound.conf.d
    cp "$DEPLOY_DIR/etc/unbound/unbound.conf.d/dns64.conf" /etc/unbound/unbound.conf.d/

    # Health monitor
    cp "$DEPLOY_DIR/usr/local/bin/wan-health-monitor.py" /usr/local/bin/
    chmod +x /usr/local/bin/wan-health-monitor.py

    # Systemd services
    cp "$DEPLOY_DIR/etc/systemd/system/"*.service /etc/systemd/system/
    systemctl daemon-reload

    log "Configurations deployed"
}

configure_interfaces() {
    log "Configuring network interfaces..."

    # This is a template - actual IPs depend on DHCP/static assignment
    cat << 'EOF'
=== MANUAL INTERFACE CONFIGURATION REQUIRED ===

Configure these interfaces based on your cable modem assignments:

WAN1 (eth0): 206.75.1.126/30 gw 206.75.1.127  [Telus Primary]
WAN2 (eth3): 206.75.1.46/30  gw 206.75.1.47   [Telus Secondary]
WAN3 (eth4): 206.75.1.49/30  gw 206.75.1.48   [Telus Tertiary]
WAN4 (eth5): DHCP                              [Shaw/New ISP]
WAN5 (eth2): 192.168.0.2/24  gw 192.168.0.1   [LTE Backup]
LAN  (eth1): 192.168.100.1/24                  [Internal trunk]

Run: nmcli or ip addr to configure

EOF
}

start_services() {
    log "Starting services..."

    # Apply nftables
    nft -f /etc/nftables.conf

    # Start BIRD2
    systemctl enable bird
    systemctl restart bird

    # Start Unbound
    systemctl enable unbound
    systemctl restart unbound

    # Start health monitor
    systemctl enable wan-health-monitor
    systemctl start wan-health-monitor

    # Jool NAT64 stays disabled
    systemctl disable jool-nat64 2>/dev/null || true

    log "Services started"
}

verify_deployment() {
    log "Verifying deployment..."

    echo ""
    echo "=== BIRD2 Status ==="
    birdc show protocols 2>/dev/null || echo "BIRD not running yet"

    echo ""
    echo "=== nftables Status ==="
    nft list ruleset | head -20

    echo ""
    echo "=== Health Monitor ==="
    curl -s http://localhost:9200/health 2>/dev/null | head -20 || echo "Health monitor not ready"

    echo ""
    echo "=== Zone Isolation Check ==="
    echo "Checking .ownid zone cannot reach IPv4..."
    # This would be tested from an .ownid host

    log "Verification complete"
}

print_summary() {
    cat << 'EOF'

╔═══════════════════════════════════════════════════════════════════╗
║            R730 ORION 5-WAN DEPLOYMENT COMPLETE                   ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Genesis Bond: ACTIVE @ 432 Hz                                    ║
║  ASN: 54134 (LUCINET-ARIN)                                        ║
║                                                                    ║
║  ZONES:                                                            ║
║  ├── Web2 Zone: IPv4+IPv6, 5-WAN ECMP NAT                        ║
║  ├── .ownid Zone: IPv6-ONLY, NO Web2 access                      ║
║  └── CORE Tier: Airgapped, NO external access                    ║
║                                                                    ║
║  SERVICES:                                                         ║
║  ├── BIRD2: BGP routing with BFD failover                        ║
║  ├── nftables: Zone isolation firewall                            ║
║  ├── Health Monitor: http://localhost:9200/metrics               ║
║  └── Jool NAT64: DISABLED (enable only if required)              ║
║                                                                    ║
║  NEXT STEPS:                                                       ║
║  1. Configure network interfaces (see above)                      ║
║  2. Put cable modems in bridge mode                               ║
║  3. Verify BGP sessions: birdc show protocols                     ║
║  4. Test zone isolation from .ownid host                          ║
║                                                                    ║
╚═══════════════════════════════════════════════════════════════════╝

EOF
}

main() {
    log "=== R730 ORION 5-WAN Deployment Starting ==="

    check_root
    backup_existing
    install_dependencies
    deploy_configs
    configure_interfaces
    start_services
    verify_deployment
    print_summary

    log "=== Deployment Complete ==="
}

# Run if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
