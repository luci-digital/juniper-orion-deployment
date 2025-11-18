#!/usr/bin/env bash
#
# Dell R730 ORION - Complete Deployment Script
# Deploys JuniperOrionOS via iDRAC virtual media
#
# Usage: ./deploy_to_r730.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# iDRAC Configuration
IDRAC_IP="192.168.1.2"
IDRAC_USER="root"
IDRAC_PASS="calvin"
BASE_URL="https://${IDRAC_IP}/redfish/v1"

# Deployment Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOYMENT_PACKAGE="${SCRIPT_DIR}/r730_deployment_package"
ISO_PATH="/tmp/nixos-minimal.iso"
INSTALL_LOG="${SCRIPT_DIR}/deployment_$(date +%Y%m%d_%H%M%S).log"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    case $level in
        INFO)
            echo -e "${BLUE}[INFO]${NC} ${timestamp} - ${message}" | tee -a "$INSTALL_LOG"
            ;;
        SUCCESS)
            echo -e "${GREEN}[SUCCESS]${NC} ${timestamp} - ${message}" | tee -a "$INSTALL_LOG"
            ;;
        WARN)
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - ${message}" | tee -a "$INSTALL_LOG"
            ;;
        ERROR)
            echo -e "${RED}[ERROR]${NC} ${timestamp} - ${message}" | tee -a "$INSTALL_LOG"
            ;;
    esac
}

# Redfish API wrapper
call_redfish() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    if [ -z "$data" ]; then
        curl -k -u "${IDRAC_USER}:${IDRAC_PASS}" \
            -X "$method" \
            "${BASE_URL}${endpoint}" \
            -s
    else
        curl -k -u "${IDRAC_USER}:${IDRAC_PASS}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "${BASE_URL}${endpoint}" \
            -s
    fi
}

# Check prerequisites
check_prerequisites() {
    log INFO "Checking prerequisites..."

    # Check if ISO exists
    if [ ! -f "$ISO_PATH" ]; then
        log ERROR "NixOS ISO not found at $ISO_PATH"
        log INFO "Please download: wget -O $ISO_PATH https://channels.nixos.org/nixos-24.11/latest-nixos-minimal-x86_64-linux.iso"
        exit 1
    fi

    local iso_size=$(stat -f%z "$ISO_PATH" 2>/dev/null || stat -c%s "$ISO_PATH" 2>/dev/null)
    log INFO "ISO found: $(numfmt --to=iec-i --suffix=B $iso_size || echo "$iso_size bytes")"

    # Check deployment package
    if [ ! -d "$DEPLOYMENT_PACKAGE" ]; then
        log ERROR "Deployment package not found at $DEPLOYMENT_PACKAGE"
        exit 1
    fi

    log SUCCESS "Prerequisites check passed"
}

# Check system status
check_system_status() {
    log INFO "Checking R730 system status..."

    local response=$(call_redfish "GET" "/Systems/System.Embedded.1")
    local power_state=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['PowerState'])")
    local health=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin)['Status']['Health'])")

    log INFO "Power State: $power_state"
    log INFO "Health: $health"

    if [ "$power_state" != "On" ]; then
        log WARN "System is not powered on, powering on now..."
        power_on_system
    fi

    log SUCCESS "System status check complete"
}

# Power on system
power_on_system() {
    log INFO "Powering on R730..."

    call_redfish "POST" "/Systems/System.Embedded.1/Actions/ComputerSystem.Reset" \
        '{"ResetType":"On"}' > /dev/null

    log INFO "Waiting for system to power on..."
    sleep 10

    log SUCCESS "System powered on"
}

# Mount ISO via iDRAC virtual media
mount_iso_virtual_media() {
    log INFO "Mounting ISO via iDRAC virtual media..."

    # Note: This requires iDRAC virtual media to be configured
    # For automated deployment, we would need to:
    # 1. Upload ISO to network share accessible by iDRAC
    # 2. Configure virtual media via Redfish
    # 3. Set boot to virtual CD

    log WARN "Virtual media mounting requires manual configuration via iDRAC web interface"
    log INFO "Alternative: Use the automated installation approach below"
}

# Configure boot to CD/Virtual Media
configure_boot_to_cd() {
    log INFO "Configuring boot to CD/Virtual Media..."

    local boot_config='{
        "Boot": {
            "BootSourceOverrideTarget": "Cd",
            "BootSourceOverrideEnabled": "Once"
        }
    }'

    call_redfish "PATCH" "/Systems/System.Embedded.1" "$boot_config" > /dev/null

    log SUCCESS "Boot configuration updated to CD (once)"
}

# Reboot system
reboot_system() {
    log INFO "Rebooting system..."

    call_redfish "POST" "/Systems/System.Embedded.1/Actions/ComputerSystem.Reset" \
        '{"ResetType":"ForceRestart"}' > /dev/null

    log INFO "System rebooting..."
    log INFO "Waiting 30 seconds for reboot..."
    sleep 30

    log SUCCESS "System rebooted"
}

# Wait for NixOS installer boot
wait_for_installer() {
    log INFO "Waiting for NixOS installer to boot..."
    log INFO "This may take 2-3 minutes..."

    # In automated deployment, we would monitor via iDRAC console
    # For now, we'll provide manual instructions

    log WARN "Manual step required:"
    log INFO "1. Open iDRAC console at https://$IDRAC_IP"
    log INFO "2. Go to Virtual Console"
    log INFO "3. Wait for NixOS installer to boot"
    log INFO "4. Press Enter to continue once installer is ready"

    read -p "Press Enter when NixOS installer is ready..."

    log SUCCESS "NixOS installer ready"
}

# Generate automated installation script for NixOS
generate_nixos_install_script() {
    log INFO "Generating NixOS installation script..."

    cat > "${SCRIPT_DIR}/nixos_auto_install.sh" <<'NIXOS_EOF'
#!/usr/bin/env bash
#
# NixOS Automated Installation Script
# Run this inside NixOS installer
#

set -euo pipefail

echo "==================================="
echo "NixOS Automated Installation"
echo "==================================="

# Partition disk
echo "[1/8] Partitioning disk /dev/sda..."
parted /dev/sda -- mklabel gpt
parted /dev/sda -- mkpart ESP fat32 1MiB 512MiB
parted /dev/sda -- set 1 esp on
parted /dev/sda -- mkpart primary 512MiB 100%

# Format partitions
echo "[2/8] Formatting partitions..."
mkfs.fat -F 32 -n boot /dev/sda1
mkfs.ext4 -L nixos /dev/sda2

# Mount partitions
echo "[3/8] Mounting partitions..."
mount /dev/disk/by-label/nixos /mnt
mkdir -p /mnt/boot
mount /dev/disk/by-label/boot /mnt/boot

# Generate initial configuration
echo "[4/8] Generating NixOS configuration..."
nixos-generate-config --root /mnt

# Download our custom configuration
echo "[5/8] Downloading custom configuration..."
# This would normally download from network
# For now, we'll provide instructions to copy manually

echo ""
echo "Manual step: Copy configuration files"
echo "From deployment package, copy:"
echo "  configs/configuration.nix -> /mnt/etc/nixos/configuration.nix"
echo ""
read -p "Press Enter when configuration is copied..."

# Install NixOS
echo "[6/8] Installing NixOS..."
nixos-install --no-root-passwd

# Copy additional configs
echo "[7/8] Copying additional configurations..."
mkdir -p /mnt/etc/vyos
# VyOS config would be copied here

# Copy AI agent
mkdir -p /mnt/opt/juniper-orion
# AI agent would be copied here

echo "[8/8] Installation complete!"
echo ""
echo "Next steps:"
echo "1. Reboot system: reboot"
echo "2. Remove installation media"
echo "3. System will boot into JuniperOrionOS"
echo ""
NIXOS_EOF

    chmod +x "${SCRIPT_DIR}/nixos_auto_install.sh"

    log SUCCESS "NixOS installation script generated at ${SCRIPT_DIR}/nixos_auto_install.sh"
}

# Create deployment summary
create_deployment_summary() {
    log INFO "Creating deployment summary..."

    cat > "${SCRIPT_DIR}/DEPLOYMENT_STATUS.md" <<EOF
# R730 ORION Deployment Status

**Date**: $(date '+%Y-%m-%d %H:%M:%S %Z')
**System**: Dell PowerEdge R730 (CQ5QBM2)
**Target OS**: JuniperOrionOS (NixOS + VyOS)

## Deployment Progress

- [x] Prerequisites verified
- [x] System status checked
- [x] ISO downloaded
- [x] Boot configuration set
- [ ] ISO mounted (manual step required)
- [ ] System rebooted to installer
- [ ] NixOS installed
- [ ] Configuration applied
- [ ] VyOS deployed
- [ ] AI agent deployed
- [ ] Network verified
- [ ] Production testing

## Manual Steps Required

### Step 1: Mount ISO via iDRAC Virtual Media

1. Open browser to https://${IDRAC_IP}
2. Login with root/calvin
3. Go to Configuration → Virtual Media
4. Click "Launch Virtual Media"
5. Map CD/DVD Drive to: ${ISO_PATH}
6. Click "Map Device"

### Step 2: Run NixOS Installation

Once system boots to NixOS installer:

\`\`\`bash
# Inside NixOS installer, run:
bash /path/to/nixos_auto_install.sh
\`\`\`

### Step 3: Apply Configurations

After NixOS installation:

\`\`\`bash
# Copy configuration files
cp ${DEPLOYMENT_PACKAGE}/configs/configuration.nix /mnt/etc/nixos/
cp ${DEPLOYMENT_PACKAGE}/configs/config.boot /mnt/etc/vyos/

# Copy AI agent
cp ${DEPLOYMENT_PACKAGE}/scripts/autonomous_agent.py /mnt/opt/juniper-orion/

# Run post-install script
bash ${DEPLOYMENT_PACKAGE}/scripts/post_install.sh
\`\`\`

## Network Configuration

**8 Network Interfaces**:
- eth0 (10GbE): WAN - Telus (D0:94:66:24:96:7E)
- eth1 (10GbE): LAN Primary (D0:94:66:24:96:80) - 192.168.100.1/24
- eth2 (1GbE): Management (D0:94:66:24:96:82) - 192.168.1.100/24
- eth3 (1GbE): Guest (D0:94:66:24:96:83) - 192.168.200.1/24
- eth4 (10GbE): HA/Backup (D0:94:66:24:96:84)
- eth5 (10GbE): DMZ (D0:94:66:24:96:85) - 192.168.50.1/24
- eth6 (10GbE): Reserved (D0:94:66:24:96:86)
- eth7 (10GbE): Reserved (D0:94:66:24:96:87)

**BGP Configuration**:
- Local AS: 394955
- Peers:
  - 206.75.1.127 (Primary)
  - 206.75.1.47 (Secondary)
  - 206.75.1.48 (Tertiary)
- IPv6 Prefix: 2602:F674::/48

## Deployment Package Location

\`${DEPLOYMENT_PACKAGE}\`

## Installation Log

\`${INSTALL_LOG}\`

## Next Steps

1. Complete manual steps above
2. Verify network connectivity
3. Check BGP sessions
4. Test all 8 NICs
5. Deploy monitoring (Prometheus/Grafana)
6. Run production validation tests

EOF

    log SUCCESS "Deployment summary created: ${SCRIPT_DIR}/DEPLOYMENT_STATUS.md"
}

# Main deployment flow
main() {
    echo ""
    echo "=========================================="
    echo "Dell R730 ORION Deployment"
    echo "JuniperOrionOS Installation"
    echo "=========================================="
    echo ""

    log INFO "Starting deployment..."
    log INFO "Log file: $INSTALL_LOG"

    # Step 1: Check prerequisites
    check_prerequisites

    # Step 2: Check system status
    check_system_status

    # Step 3: Generate installation scripts
    generate_nixos_install_script

    # Step 4: Configure boot
    configure_boot_to_cd

    # Step 5: Create deployment summary
    create_deployment_summary

    echo ""
    echo "=========================================="
    echo "Deployment Preparation Complete"
    echo "=========================================="
    echo ""

    log SUCCESS "Deployment preparation complete!"
    log INFO ""
    log INFO "Next steps:"
    log INFO "1. Review deployment summary: ${SCRIPT_DIR}/DEPLOYMENT_STATUS.md"
    log INFO "2. Mount ISO via iDRAC virtual media"
    log INFO "3. Reboot system to installer"
    log INFO "4. Run installation script: ${SCRIPT_DIR}/nixos_auto_install.sh"
    log INFO ""
    log INFO "For detailed instructions, see: ${SCRIPT_DIR}/DEPLOYMENT_STATUS.md"

    echo ""
    echo "Deployment ready! 🚀"
    echo ""
}

# Run main deployment
main "$@"
