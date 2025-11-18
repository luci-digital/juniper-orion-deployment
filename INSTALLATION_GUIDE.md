# Dell R730 JuniperOrionOS Installation Guide

**Generated**: 2025-11-18 13:24:07
**System**: Dell PowerEdge R730 (CQ5QBM2)
**Target**: JuniperOrionOS (NixOS + VyOS + AI Agent)

## Current Status

✅ ISO Downloaded: /tmp/nixos-minimal.iso (510.2 MB)
✅ Deployment Package Ready: /Users/darylharr/Desktop/dis_maops/r730_deployment_package
✅ Boot Configured: CD/Virtual Media (once)

## Installation Steps

### Option 1: Manual Installation (Recommended)

#### Step 1: Mount ISO via iDRAC

1. Open browser to **https://192.168.1.2**
2. Login with **root / calvin**
3. Navigate to **Configuration → Virtual Media**
4. Click **"Launch Virtual Media"**
5. Map CD/DVD Drive to: **/tmp/nixos-minimal.iso**
6. Click **"Map Device"**

#### Step 2: Reboot to Installer

System is already configured to boot from CD once. Reboot via iDRAC:

1. Go to **Dashboard → Power/Thermal**
2. Click **"Power On/Off"** → **"Reboot System"**

Or use command line:
```bash
python3 automated_r730_deploy.py --reboot
```

#### Step 3: Wait for NixOS Installer

1. Open **Virtual Console** in iDRAC
2. Wait for NixOS installer to boot (2-3 minutes)
3. You should see NixOS welcome screen

#### Step 4: Partition and Install

In NixOS installer console:

```bash
# Partition disk
parted /dev/sda -- mklabel gpt
parted /dev/sda -- mkpart ESP fat32 1MiB 512MiB
parted /dev/sda -- set 1 esp on
parted /dev/sda -- mkpart primary 512MiB 100%

# Format
mkfs.fat -F 32 -n boot /dev/sda1
mkfs.ext4 -L nixos /dev/sda2

# Mount
mount /dev/disk/by-label/nixos /mnt
mkdir -p /mnt/boot
mount /dev/disk/by-label/boot /mnt/boot

# Generate config
nixos-generate-config --root /mnt
```

#### Step 5: Apply Custom Configuration

The deployment package contains optimized configuration. Transfer it:

**Via network (if available)**:
```bash
# On your workstation
scp /Users/darylharr/Desktop/dis_maops/r730_deployment_package/configs/configuration.nix nixos@R730_IP:/tmp/

# On R730 installer
mv /tmp/configuration.nix /mnt/etc/nixos/
```

**Via copy-paste in console**:
1. Open configuration file locally
2. Use iDRAC virtual console clipboard
3. Paste into nano/vi on installer

#### Step 6: Install NixOS

```bash
nixos-install

# Set root password when prompted
```

#### Step 7: Post-Installation Configuration

After reboot into new system:

```bash
# Copy VyOS configuration
mkdir -p /etc/vyos
# Transfer config.boot from deployment package

# Copy AI agent
mkdir -p /opt/juniper-orion
# Transfer autonomous_agent.py

# Install additional packages
nix-env -iA nixos.python3
nix-env -iA nixos.prometheus
nix-env -iA nixos.grafana

# Start AI agent
systemctl enable juniper-ai-agent
systemctl start juniper-ai-agent
```

### Option 2: PXE Network Boot (Advanced)

If you have a PXE server on network:

1. Configure DHCP to serve NixOS installer
2. System is already set for PXE boot
3. Reboot and installer will load from network

## Network Configuration

Once installed, the system will have:

**8 Network Interfaces**:
- **eth0** (10GbE) - WAN: Telus (MAC: D0:94:66:24:96:7E)
- **eth1** (10GbE) - LAN: 192.168.100.1/24 (MAC: D0:94:66:24:96:80)
- **eth2** (1GbE) - Management: 192.168.1.100/24 (MAC: D0:94:66:24:96:82)
- **eth3** (1GbE) - Guest: 192.168.200.1/24 (MAC: D0:94:66:24:96:83)
- **eth4** (10GbE) - HA/Backup (MAC: D0:94:66:24:96:84)
- **eth5** (10GbE) - DMZ: 192.168.50.1/24 (MAC: D0:94:66:24:96:85)
- **eth6** (10GbE) - Reserved (MAC: D0:94:66:24:96:86)
- **eth7** (10GbE) - Reserved (MAC: D0:94:66:24:96:87)

**BGP Routing**:
- Local AS: **394955**
- Telus Peers:
  - 206.75.1.127 (Primary)
  - 206.75.1.47 (Secondary)
  - 206.75.1.48 (Tertiary)
- IPv6: **2602:F674::/48**

## Verification

After installation:

```bash
# Check NICs
ip link show

# Check routing
ip route show
ip -6 route show

# Check BGP sessions
vtysh -c "show ip bgp summary"

# Check AI agent
systemctl status juniper-ai-agent

# Check monitoring
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
```

## Troubleshooting

**Issue**: ISO won't boot
- Verify virtual media is mounted
- Check boot order in BIOS
- Ensure CD is set as boot target

**Issue**: Network not working
- Verify MAC addresses match configuration
- Check cable connections
- Verify switch/router configuration

**Issue**: BGP sessions won't establish
- Verify Telus modem is in bridge mode
- Check WAN interface has IP
- Verify AS number 394955 is correct

## Files and Locations

- **Deployment Package**: `/Users/darylharr/Desktop/dis_maops/r730_deployment_package`
- **NixOS Config**: `/Users/darylharr/Desktop/dis_maops/r730_deployment_package/configs/configuration.nix`
- **VyOS Config**: `/Users/darylharr/Desktop/dis_maops/r730_deployment_package/configs/config.boot`
- **AI Agent**: `/Users/darylharr/Desktop/dis_maops/r730_deployment_package/scripts/autonomous_agent.py`
- **Post-Install**: `/Users/darylharr/Desktop/dis_maops/r730_deployment_package/scripts/post_install.sh`

## Support

For detailed configuration reference:
- See `R730_DEPLOYMENT_COMPLETE.md`
- See `ENZYME_SYSTEM_INTEGRATION.md`
- See deployment logs in current directory

---

**Status**: Ready for manual installation via iDRAC virtual media
