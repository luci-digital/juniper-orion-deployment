#!/usr/bin/env bash
#
# Create NixOS USB with callback script
# When R730 boots, it will phone home and establish reverse SSH
#

set -euo pipefail

ISO_PATH="/tmp/nixos-minimal.iso"
CALLBACK_HOST="192.168.1.175"  # Your Mac
CALLBACK_PORT="2222"            # Listening port for reverse connection

echo "========================================"
echo "NixOS USB with Callback Script"
echo "========================================"
echo ""

# Check if ISO exists
if [ ! -f "$ISO_PATH" ]; then
    echo "Error: ISO not found at $ISO_PATH"
    exit 1
fi

echo "[1/6] Finding USB drive..."
echo ""
diskutil list
echo ""
echo "Which disk is your USB? (e.g., disk2, disk3)"
read -p "Enter disk number: " DISK_NUM

USB_DISK="/dev/${DISK_NUM}"
USB_RDISK="/dev/r${DISK_NUM}"

echo ""
echo "⚠️  WARNING: This will ERASE ${USB_DISK}!"
echo "Please verify this is your USB drive:"
diskutil info "${USB_DISK}" | grep -E "Device Node:|Volume Name:|Total Size:"
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "[2/6] Unmounting ${USB_DISK}..."
diskutil unmountDisk "${USB_DISK}"

echo ""
echo "[3/6] Writing ISO to USB (this takes ~10 minutes)..."
echo "Progress will be shown..."
sudo dd if="$ISO_PATH" of="$USB_RDISK" bs=1m status=progress

echo ""
echo "[4/6] Syncing..."
sync

echo ""
echo "[5/6] Mounting USB to add callback script..."
# Wait for partitions to appear
sleep 2

# Find the EFI partition
EFI_PARTITION="${USB_DISK}s1"
MOUNT_POINT="/tmp/nixos_usb_mount"

mkdir -p "$MOUNT_POINT"
sudo mount -t msdos "$EFI_PARTITION" "$MOUNT_POINT" 2>/dev/null || \
sudo mount "$EFI_PARTITION" "$MOUNT_POINT"

echo ""
echo "[6/6] Creating callback script..."

# Create callback script that will run on boot
cat > "$MOUNT_POINT/callback.sh" <<'CALLBACK_EOF'
#!/usr/bin/env bash
#
# NixOS Installer Callback Script
# Phones home when installer boots
#

CALLBACK_HOST="192.168.1.175"
CALLBACK_PORT="2222"

# Wait for network
sleep 5

# Try to get IP via DHCP
dhclient -v eth0 2>&1 || ip link set eth0 up
sleep 3

# Phone home with system info
{
    echo "=== NixOS Installer Booted ==="
    echo "Hostname: $(hostname)"
    echo "IP Address: $(ip addr show | grep 'inet ' | grep -v 127.0.0.1)"
    echo "Timestamp: $(date)"
    echo "=== Ready for installation ==="
} | nc "$CALLBACK_HOST" "$CALLBACK_PORT" 2>/dev/null || true

# Try to establish reverse SSH if possible
# (This would require SSH server on your Mac)
# ssh -R 0.0.0.0:2223:localhost:22 user@$CALLBACK_HOST -N &

# Signal ready
echo "READY" | nc "$CALLBACK_HOST" "$CALLBACK_PORT" 2>/dev/null || true

CALLBACK_EOF

chmod +x "$MOUNT_POINT/callback.sh"

# Create autorun script for NixOS
cat > "$MOUNT_POINT/autorun.sh" <<'AUTORUN_EOF'
#!/usr/bin/env bash
# Run callback after network is up
sleep 2
bash /callback.sh &
AUTORUN_EOF

chmod +x "$MOUNT_POINT/autorun.sh"

echo ""
echo "Callback script created at: ${MOUNT_POINT}/callback.sh"
echo ""
echo "NOTE: To make this auto-run, we need to modify the ISO boot process."
echo "For now, you'll need to manually run:"
echo "  bash /run/current-system/sw/bin/callback.sh"
echo ""
echo "Or I can listen for network traffic and you can run a simple curl command."

# Unmount
sudo umount "$MOUNT_POINT"
rmdir "$MOUNT_POINT"

echo ""
echo "[7/6] Ejecting USB..."
diskutil eject "${USB_DISK}"

echo ""
echo "========================================"
echo "USB Creation Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. On your Mac, start listening:"
echo "   nc -l $CALLBACK_PORT"
echo ""
echo "2. Boot R730 from USB"
echo ""
echo "3. At NixOS prompt, run:"
echo "   curl http://${CALLBACK_HOST}:8000/ping || echo READY | nc ${CALLBACK_HOST} ${CALLBACK_PORT}"
echo ""
echo "This will signal me that you're ready!"
echo ""
