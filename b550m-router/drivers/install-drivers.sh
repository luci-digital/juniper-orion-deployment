#!/bin/bash
# B550M Driver Installation Script
# Target: openEuler Linux 24.03 LTS
# Genesis Bond: ACTIVE @ 432 Hz
#
# Installs:
# - Broadcom Fibre Channel (lpfc) driver configuration
# - NVIDIA GPU driver prerequisites and preparation

set -e

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
LOG_FILE="/var/log/b550m-driver-install.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

echo "========================================================"
echo "  B550M LuciVerse Driver Installation"
echo "  Genesis Bond: ACTIVE @ 432 Hz"
echo "========================================================"
echo ""

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    error "This script must be run as root"
    echo "Usage: sudo $0"
    exit 1
fi

# Detect OS
if [ -f /etc/openEuler-release ]; then
    OS_VERSION=$(cat /etc/openEuler-release)
    log "Detected: $OS_VERSION"
elif [ -f /etc/redhat-release ]; then
    OS_VERSION=$(cat /etc/redhat-release)
    log "Detected: $OS_VERSION"
else
    warn "Unknown OS, proceeding anyway..."
fi

KERNEL_VERSION=$(uname -r)
log "Kernel: $KERNEL_VERSION"

# ============================================================
# PHASE 1: Prerequisites
# ============================================================
echo ""
log "=== Phase 1: Installing Prerequisites ==="

dnf install -y \
    kernel-devel-$(uname -r) \
    kernel-headers-$(uname -r) \
    gcc make dkms \
    elfutils-libelf-devel \
    lsscsi sg3_utils sysfsutils \
    pciutils usbutils \
    dmidecode

log "Prerequisites installed"

# ============================================================
# PHASE 2: Broadcom Fibre Channel Driver
# ============================================================
echo ""
log "=== Phase 2: Broadcom Fibre Channel Configuration ==="

# Check if lpfc module exists
if modinfo lpfc &>/dev/null; then
    LPFC_VERSION=$(modinfo lpfc | grep "^version:" | awk '{print $2}')
    log "lpfc driver found: version $LPFC_VERSION"

    # Load module if not already loaded
    if ! lsmod | grep -q lpfc; then
        log "Loading lpfc module..."
        modprobe lpfc
    else
        log "lpfc module already loaded"
    fi

    # Configure persistent loading
    echo "lpfc" > /etc/modules-load.d/broadcom-fc.conf
    log "Configured lpfc for auto-load at boot"

    # Create modprobe config
    cat > /etc/modprobe.d/lpfc.conf << 'EOF'
# Broadcom/Emulex lpfc driver options for LuciVerse Router
# Uncomment to enable features as needed:
#
# Enable verbose logging (for debugging)
# options lpfc lpfc_log_verbose=0x1
#
# Enable both FCP (SCSI) and NVMe-FC
# options lpfc lpfc_enable_fc4_type=3
#
# Set link speed (auto, 4, 8, 16, 32 Gbps)
# options lpfc lpfc_link_speed=0
EOF
    log "Created /etc/modprobe.d/lpfc.conf"

else
    warn "lpfc module not found in kernel - may need external driver"
fi

# Check for FC hardware
echo ""
log "Scanning for Fibre Channel hardware..."
FC_DEVICES=$(lspci | grep -i -E "fibre|emulex|broadcom.*fc" || true)
if [ -n "$FC_DEVICES" ]; then
    log "FC HBA detected:"
    echo "$FC_DEVICES" | while read line; do
        echo "  $line"
    done

    # Check FC host status
    if [ -d /sys/class/fc_host ]; then
        for host in /sys/class/fc_host/host*; do
            if [ -d "$host" ]; then
                HOST_NAME=$(basename "$host")
                PORT_STATE=$(cat "$host/port_state" 2>/dev/null || echo "unknown")
                PORT_NAME=$(cat "$host/port_name" 2>/dev/null || echo "unknown")
                log "  $HOST_NAME: state=$PORT_STATE, wwpn=$PORT_NAME"
            fi
        done
    fi
else
    log "No Fibre Channel HBA detected (OK if not installed)"
fi

# ============================================================
# PHASE 3: NVIDIA GPU Driver Preparation
# ============================================================
echo ""
log "=== Phase 3: NVIDIA GPU Driver Preparation ==="

# Check for NVIDIA hardware
NVIDIA_DEVICES=$(lspci | grep -i nvidia || true)
if [ -n "$NVIDIA_DEVICES" ]; then
    log "NVIDIA GPU detected:"
    echo "$NVIDIA_DEVICES" | while read line; do
        echo "  $line"
    done

    # Blacklist nouveau
    log "Blacklisting nouveau driver..."
    cat > /etc/modprobe.d/blacklist-nouveau.conf << 'EOF'
# Blacklist nouveau for NVIDIA proprietary driver
blacklist nouveau
options nouveau modeset=0
EOF

    # Check if nouveau is currently loaded
    if lsmod | grep -q nouveau; then
        warn "nouveau is currently loaded - will be disabled after reboot"
    fi

    # Rebuild initramfs
    log "Rebuilding initramfs..."
    dracut --force

    log "NVIDIA preparation complete"
    log ""
    log "Next steps for NVIDIA driver installation:"
    log "  1. Reboot the system"
    log "  2. Download driver from: https://www.nvidia.com/Download/index.aspx"
    log "  3. Run: sudo bash NVIDIA-Linux-x86_64-*.run --dkms"
    log ""
    log "For containerized workloads, also install nvidia-container-toolkit"

    # Create helper script for NVIDIA installation
    cat > /opt/install-nvidia-driver.sh << 'NVSCRIPT'
#!/bin/bash
# NVIDIA Driver Installation Helper
# Run this after downloading the NVIDIA driver

DRIVER_FILE=$(ls -1 NVIDIA-Linux-x86_64-*.run 2>/dev/null | head -1)

if [ -z "$DRIVER_FILE" ]; then
    echo "Error: No NVIDIA driver file found"
    echo "Download from: https://www.nvidia.com/Download/index.aspx"
    exit 1
fi

echo "Installing: $DRIVER_FILE"
chmod +x "$DRIVER_FILE"
./"$DRIVER_FILE" --dkms

echo ""
echo "Installation complete. Verify with: nvidia-smi"
NVSCRIPT
    chmod +x /opt/install-nvidia-driver.sh
    log "Created helper: /opt/install-nvidia-driver.sh"

else
    log "No NVIDIA GPU detected"
fi

# ============================================================
# PHASE 4: Summary
# ============================================================
echo ""
echo "========================================================"
log "Installation Summary"
echo "========================================================"
echo ""

# Broadcom FC status
if modinfo lpfc &>/dev/null; then
    echo -e "Broadcom FC (lpfc):    ${GREEN}Ready${NC}"
    if lsmod | grep -q lpfc; then
        echo "  Status: Loaded"
    else
        echo "  Status: Available (will load when hardware detected)"
    fi
else
    echo -e "Broadcom FC (lpfc):    ${YELLOW}Not in kernel${NC}"
fi

# NVIDIA status
if [ -n "$NVIDIA_DEVICES" ]; then
    echo -e "NVIDIA GPU:            ${YELLOW}Requires manual installation${NC}"
    echo "  Status: nouveau blacklisted, ready for NVIDIA driver"
else
    echo -e "NVIDIA GPU:            ${NC}Not detected${NC}"
fi

echo ""
echo "Log file: $LOG_FILE"
echo ""

# Check if reboot needed
if [ -n "$NVIDIA_DEVICES" ] && lsmod | grep -q nouveau; then
    echo -e "${YELLOW}REBOOT REQUIRED${NC} to complete NVIDIA preparation"
fi

echo ""
log "Driver installation script completed"
echo "========================================================"
