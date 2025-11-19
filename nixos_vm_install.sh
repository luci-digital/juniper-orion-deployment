#!/usr/bin/env bash
#
# NixOS VM Installation Script
# For VMs running on openEuler/KVM
#

set -euo pipefail

CONFIG_SERVER="http://192.168.1.175:8000"
CALLBACK_SERVER="http://192.168.1.175:9999"

echo "========================================"
echo "NixOS VM Router Installer"
echo "========================================"
echo ""

# Send initial callback
echo "[1/10] Sending callback..."
curl -s "${CALLBACK_SERVER}/vm-install-started" || echo "Callback sent (or failed)"

# Detect VM disk (should be /dev/vda for KVM)
echo ""
echo "[2/10] Detecting disks..."
if [ -b /dev/vda ]; then
    DISK="/dev/vda"
elif [ -b /dev/sda ]; then
    DISK="/dev/sda"
else
    echo "Error: No suitable disk found!"
    lsblk
    exit 1
fi

echo "Installing to: $DISK"
lsblk "$DISK"

# Partition disk
echo ""
echo "[3/10] Partitioning $DISK..."
parted "$DISK" -- mklabel gpt
parted "$DISK" -- mkpart ESP fat32 1MiB 512MiB
parted "$DISK" -- set 1 esp on
parted "$DISK" -- mkpart primary 512MiB 100%

# Determine partition names (VMs use vdaX, not vdapX)
if [[ "$DISK" == /dev/vd* ]]; then
    BOOT_PART="${DISK}1"
    ROOT_PART="${DISK}2"
elif [[ "$DISK" == /dev/nvme* ]]; then
    BOOT_PART="${DISK}p1"
    ROOT_PART="${DISK}p2"
else
    BOOT_PART="${DISK}1"
    ROOT_PART="${DISK}2"
fi

# Format partitions
echo ""
echo "[4/10] Formatting partitions..."
mkfs.fat -F 32 -n boot "$BOOT_PART"
mkfs.ext4 -L nixos "$ROOT_PART"

# Mount filesystems
echo ""
echo "[5/10] Mounting filesystems..."
mount /dev/disk/by-label/nixos /mnt
mkdir -p /mnt/boot
mount /dev/disk/by-label/boot /mnt/boot

# Generate base config
echo ""
echo "[6/10] Generating NixOS configuration..."
nixos-generate-config --root /mnt

# Download custom configuration
echo ""
echo "[7/10] Downloading JuniperOrionOS router configuration..."
curl -o /tmp/configuration.nix "${CONFIG_SERVER}/r730_deployment_package/configs/configuration.nix" || {
    echo "Warning: Could not download custom config, using generated config"
}

# If download succeeded, use custom config
if [ -f /tmp/configuration.nix ]; then
    echo "Using custom JuniperOrionOS configuration..."
    cp /tmp/configuration.nix /mnt/etc/nixos/configuration.nix
else
    echo "Using generated configuration..."
fi

# Install NixOS
echo ""
echo "[8/10] Installing NixOS (this takes ~15 minutes)..."
curl -s "${CALLBACK_SERVER}/nixos-install-started" || true

nixos-install --no-root-passwd

# Download post-install files
echo ""
echo "[9/10] Downloading additional configurations..."
mkdir -p /mnt/root/juniper-orion

curl -o /mnt/root/juniper-orion/config.boot \
    "${CONFIG_SERVER}/r730_deployment_package/configs/config.boot" || true
curl -o /mnt/root/juniper-orion/autonomous_agent.py \
    "${CONFIG_SERVER}/r730_deployment_package/scripts/autonomous_agent.py" || true
curl -o /mnt/root/juniper-orion/post_install.sh \
    "${CONFIG_SERVER}/r730_deployment_package/scripts/post_install.sh" || true

chmod +x /mnt/root/juniper-orion/*.sh 2>/dev/null || true

# Create README
cat > /mnt/root/juniper-orion/README.txt <<'EOF'
JuniperOrionOS VM Installation Complete!

Next steps after reboot:
1. Exit this console (Ctrl+])
2. From openEuler host: virsh console nixos-router
3. Login as root (no password set - you'll be prompted)
4. Run: bash /root/juniper-orion/post_install.sh
5. Configure VyOS routing

Network Configuration:
- VM is on virbr0 (192.168.122.x/24)
- Need to bridge physical NICs for WAN/LAN routing
- 8 NICs available on host for passthrough

Documentation: /Users/darylharr/Desktop/dis_maops/
EOF

echo ""
echo "[10/10] Sending completion callback..."
curl -s "${CALLBACK_SERVER}/vm-install-complete" || true

echo ""
echo "========================================"
echo "VM Installation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Exit console: Press Ctrl+]"
echo "2. Restart VM: virsh destroy nixos-router && virsh start nixos-router"
echo "3. Connect: virsh console nixos-router"
echo "4. Login as root"
echo "5. Run: bash /root/juniper-orion/post_install.sh"
echo ""
echo "See /root/juniper-orion/README.txt for details"
echo ""
