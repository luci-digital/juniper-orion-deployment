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
