# Dell R730 ORION Installation Summary

**Date**: Tue Nov 18 13:00:32 MST 2025
**System**: Dell PowerEdge R730 (Service Tag: CQ5QBM2)
**Installation Method**: Automated via iDRAC Redfish API

## Installation Steps Completed

1. ✓ System powered on
2. ✓ Boot order configured (PXE)
3. ✓ Installation directory created: /tmp/r730_install_20251118_130032
4. ✓ Configuration files staged
5. ✓ Deployment manifest generated
6. ✓ Post-installation script created
7. ✓ NixOS ISO prepared
8. ✓ Installation summary created

## Next Manual Steps Required

### Step 1: Setup PXE Boot Server

Since we're using network installation, you need to setup a PXE boot server:

```bash
# Option A: Use another machine as PXE server
# Install dnsmasq for DHCP + TFTP
sudo apt-get install dnsmasq pxelinux syslinux

# Configure dnsmasq
sudo nano /etc/dnsmasq.conf
# Add:
# dhcp-range=192.168.1.50,192.168.1.150,12h
# dhcp-boot=pxelinux.0
# enable-tftp
# tftp-root=/tftpboot

# Extract NixOS kernel and initrd
mkdir -p /tftpboot/nixos
mount -o loop nixos-minimal.iso /mnt
cp /mnt/boot/bzImage /tftpboot/nixos/
cp /mnt/boot/initrd /tftpboot/nixos/
```

### Step 2: Alternative - Use iDRAC Virtual Media

Simpler approach - mount ISO via iDRAC:

1. Open iDRAC web console: https://192.168.1.2
2. Navigate to: Virtual Console → Launch Virtual Console
3. Go to: Virtual Media → Connect Virtual Media
4. Map CD/DVD to NixOS ISO file
5. Reboot system (will boot from virtual CD)

### Step 3: During NixOS Installation

Once booted into NixOS installer:

```bash
# Partition disks
parted /dev/sda -- mklabel gpt
parted /dev/sda -- mkpart ESP fat32 1MiB 512MiB
parted /dev/sda -- set 1 esp on
parted /dev/sda -- mkpart primary 512MiB 100%

# Format partitions
mkfs.fat -F 32 -n boot /dev/sda1
mkfs.ext4 -L nixos /dev/sda2

# Mount
mount /dev/disk/by-label/nixos /mnt
mkdir -p /mnt/boot
mount /dev/disk/by-label/boot /mnt/boot

# Copy configuration
curl http://YOUR_IP:8000/configuration.nix -o /mnt/etc/nixos/configuration.nix

# Install
nixos-install

# Reboot
reboot
```

### Step 4: Post-Installation Configuration

After NixOS boots:

```bash
# SSH into the system
ssh admin@192.168.1.100

# Run post-installation script
sudo bash /opt/post_install.sh

# Verify network interfaces
ip addr show

# Test connectivity
ping -c 3 8.8.8.8
ping6 -c 3 2001:4860:4860::8888

# Check BGP status
birdc show protocols

# Deploy VyOS configuration
sudo vyos-config-load /opt/config.boot
```

### Step 5: Deploy AI Agent

```bash
# Install dependencies
pip3 install prometheus-client anthropic openai

# Start autonomous agent
sudo systemctl start autonomous-agent
sudo systemctl enable autonomous-agent

# Check agent status
sudo systemctl status autonomous-agent

# View agent logs
sudo journalctl -u autonomous-agent -f
```

### Step 6: Setup Monitoring

```bash
# Start Prometheus
sudo systemctl start prometheus
sudo systemctl enable prometheus

# Start Grafana
sudo systemctl start grafana
sudo systemctl enable grafana

# Access dashboards
# Grafana: http://192.168.100.1:3000
# Prometheus: http://192.168.100.1:9090
```

## Configuration Files

All configuration files are in: /tmp/r730_install_20251118_130032/configs/

- `configuration.nix` - NixOS system configuration
- `config.boot` - VyOS router configuration
- `autonomous_agent.py` - AI agent script

## Network Configuration

**WAN (Telus)**:
- Interface: eth0 (D0:94:66:24:96:7E)
- Mode: DHCP (from Telus)
- IPv6: DHCPv6-PD (prefix delegation)

**LAN**:
- Interface: eth1 (D0:94:66:24:96:80)
- IPv4: 192.168.100.1/24
- IPv6: 2602:F674:1000::1/64
- DHCP: 192.168.100.100-200

**Management**:
- Interface: eth2 (D0:94:66:24:96:82)
- IPv4: 192.168.1.100/24

**BGP**:
- Local AS: 394955
- Neighbors:
  - 206.75.1.127 (Telus Gateway 1)
  - 206.75.1.47 (Telus Gateway 2)
  - 206.75.1.48 (Telus Gateway 3)

## Troubleshooting

### System won't boot from PXE
- Check BIOS boot order
- Verify PXE server is running
- Check network connectivity

### No network connectivity
- Verify cable connections
- Check interface status: `ip link show`
- Check routing: `ip route show`

### BGP not establishing
- Verify Telus gateway IPs
- Check firewall rules
- View BGP logs: `journalctl -u bird2`

### AI agent not running
- Check logs: `journalctl -u autonomous-agent`
- Verify Python dependencies
- Check API keys in environment

## Support

- iDRAC Console: https://192.168.1.2
- System Documentation: /Users/darylharr/Desktop/dis_maops/DELL_R730_ORION_REPORT.md
- Configuration Repository: /Users/darylharr/workspace/Dell_R730_CQ5QBM2_ORION/

