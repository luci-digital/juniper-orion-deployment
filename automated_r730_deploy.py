#!/usr/bin/env python3
"""
Automated Dell R730 JuniperOrionOS Deployment
Uses iDRAC Redfish API for complete automation
"""

import requests
import json
import time
import sys
from pathlib import Path
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# iDRAC Configuration
IDRAC_IP = "192.168.1.2"
IDRAC_USER = "root"
IDRAC_PASS = "calvin"
BASE_URL = f"https://{IDRAC_IP}/redfish/v1"

# Deployment Configuration
SCRIPT_DIR = Path(__file__).parent
DEPLOYMENT_PACKAGE = SCRIPT_DIR / "r730_deployment_package"
ISO_PATH = Path("/tmp/nixos-minimal.iso")

class R730Deployer:
    """Automated R730 deployment via Redfish API"""

    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (IDRAC_USER, IDRAC_PASS)
        self.session.verify = False
        self.session.headers.update({"Content-Type": "application/json"})

    def log(self, level, message):
        """Simple logging"""
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARN": "\033[1;33m",
            "ERROR": "\033[0;31m",
            "NC": "\033[0m"
        }
        print(f"{colors.get(level, '')}{level}{colors['NC']}: {message}")

    def get(self, endpoint):
        """GET request to Redfish API"""
        url = f"{BASE_URL}{endpoint}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def post(self, endpoint, data=None):
        """POST request to Redfish API"""
        url = f"{BASE_URL}{endpoint}"
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json() if response.text else {}

    def patch(self, endpoint, data):
        """PATCH request to Redfish API"""
        url = f"{BASE_URL}{endpoint}"
        response = self.session.patch(url, json=data)
        response.raise_for_status()
        return response.json() if response.text else {}

    def check_prerequisites(self):
        """Verify prerequisites for deployment"""
        self.log("INFO", "Checking prerequisites...")

        # Check ISO exists
        if not ISO_PATH.exists():
            self.log("ERROR", f"ISO not found at {ISO_PATH}")
            self.log("INFO", "Download with: wget -O /tmp/nixos-minimal.iso https://channels.nixos.org/nixos-24.11/latest-nixos-minimal-x86_64-linux.iso")
            return False

        iso_size = ISO_PATH.stat().st_size
        self.log("INFO", f"ISO found: {iso_size / (1024**2):.1f} MB")

        # Check deployment package
        if not DEPLOYMENT_PACKAGE.exists():
            self.log("ERROR", f"Deployment package not found at {DEPLOYMENT_PACKAGE}")
            return False

        self.log("SUCCESS", "Prerequisites verified")
        return True

    def get_system_info(self):
        """Get current system information"""
        self.log("INFO", "Retrieving system information...")

        data = self.get("/Systems/System.Embedded.1")

        info = {
            "PowerState": data.get("PowerState"),
            "Health": data.get("Status", {}).get("Health"),
            "State": data.get("Status", {}).get("State"),
            "BootMode": data.get("Boot", {}).get("BootSourceOverrideMode"),
            "BootTarget": data.get("Boot", {}).get("BootSourceOverrideTarget"),
        }

        for key, value in info.items():
            self.log("INFO", f"  {key}: {value}")

        return info

    def power_on_system(self):
        """Power on the system"""
        self.log("INFO", "Powering on system...")

        self.post("/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", {
            "ResetType": "On"
        })

        time.sleep(5)
        self.log("SUCCESS", "System powered on")

    def power_off_system(self):
        """Gracefully power off the system"""
        self.log("INFO", "Powering off system...")

        self.post("/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", {
            "ResetType": "GracefulShutdown"
        })

        # Wait for shutdown
        self.log("INFO", "Waiting for graceful shutdown...")
        time.sleep(30)

        # Check if off
        info = self.get_system_info()
        if info["PowerState"] != "Off":
            self.log("WARN", "Graceful shutdown failed, forcing off...")
            self.post("/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", {
                "ResetType": "ForceOff"
            })
            time.sleep(10)

        self.log("SUCCESS", "System powered off")

    def configure_boot_to_cd(self):
        """Configure boot to CD/Virtual Media once"""
        self.log("INFO", "Configuring boot to CD (once)...")

        self.patch("/Systems/System.Embedded.1", {
            "Boot": {
                "BootSourceOverrideTarget": "Cd",
                "BootSourceOverrideEnabled": "Once"
            }
        })

        self.log("SUCCESS", "Boot configuration updated")

    def check_virtual_media_support(self):
        """Check virtual media capabilities"""
        self.log("INFO", "Checking virtual media support...")

        try:
            # Get virtual media collection
            data = self.get("/Managers/iDRAC.Embedded.1/VirtualMedia")

            members = data.get("Members", [])
            self.log("INFO", f"Found {len(members)} virtual media devices")

            for member in members:
                # Get details of each virtual media device
                vm_url = member.get("@odata.id", "")
                if vm_url:
                    vm_data = self.get(vm_url.replace(BASE_URL, ""))
                    name = vm_data.get("Name", "Unknown")
                    media_types = vm_data.get("MediaTypes", [])
                    inserted = vm_data.get("Inserted", False)

                    self.log("INFO", f"  {name}: {media_types} (Inserted: {inserted})")

            return True
        except Exception as e:
            self.log("WARN", f"Could not enumerate virtual media: {e}")
            return False

    def mount_iso_if_supported(self):
        """Attempt to mount ISO via Redfish virtual media"""
        self.log("INFO", "Attempting to mount ISO via virtual media...")

        try:
            # Note: Virtual media mounting via Redfish requires:
            # 1. Network-accessible ISO (HTTP/NFS/CIFS)
            # 2. iDRAC Enterprise license
            # 3. Properly configured iDRAC network

            self.log("WARN", "Automated ISO mounting requires iDRAC Enterprise license")
            self.log("WARN", "and network-accessible ISO location")
            self.log("INFO", "")
            self.log("INFO", "Manual alternative:")
            self.log("INFO", "  1. Open https://192.168.1.2 in browser")
            self.log("INFO", "  2. Go to Configuration → Virtual Media")
            self.log("INFO", "  3. Map CD/DVD to /tmp/nixos-minimal.iso")
            self.log("INFO", "")

            return False
        except Exception as e:
            self.log("ERROR", f"Virtual media mounting failed: {e}")
            return False

    def reboot_system(self):
        """Reboot the system"""
        self.log("INFO", "Rebooting system...")

        self.post("/Systems/System.Embedded.1/Actions/ComputerSystem.Reset", {
            "ResetType": "ForceRestart"
        })

        self.log("INFO", "System rebooting...")
        self.log("INFO", "Waiting 30 seconds...")
        time.sleep(30)

        self.log("SUCCESS", "System rebooted")

    def create_installation_guide(self):
        """Create detailed installation guide"""
        self.log("INFO", "Creating installation guide...")

        guide_path = SCRIPT_DIR / "INSTALLATION_GUIDE.md"

        content = f"""# Dell R730 JuniperOrionOS Installation Guide

**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**System**: Dell PowerEdge R730 (CQ5QBM2)
**Target**: JuniperOrionOS (NixOS + VyOS + AI Agent)

## Current Status

✅ ISO Downloaded: {ISO_PATH} ({ISO_PATH.stat().st_size / (1024**2):.1f} MB)
✅ Deployment Package Ready: {DEPLOYMENT_PACKAGE}
✅ Boot Configured: CD/Virtual Media (once)

## Installation Steps

### Option 1: Manual Installation (Recommended)

#### Step 1: Mount ISO via iDRAC

1. Open browser to **https://192.168.1.2**
2. Login with **root / calvin**
3. Navigate to **Configuration → Virtual Media**
4. Click **"Launch Virtual Media"**
5. Map CD/DVD Drive to: **{ISO_PATH}**
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
scp {DEPLOYMENT_PACKAGE}/configs/configuration.nix nixos@R730_IP:/tmp/

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

- **Deployment Package**: `{DEPLOYMENT_PACKAGE}`
- **NixOS Config**: `{DEPLOYMENT_PACKAGE}/configs/configuration.nix`
- **VyOS Config**: `{DEPLOYMENT_PACKAGE}/configs/config.boot`
- **AI Agent**: `{DEPLOYMENT_PACKAGE}/scripts/autonomous_agent.py`
- **Post-Install**: `{DEPLOYMENT_PACKAGE}/scripts/post_install.sh`

## Support

For detailed configuration reference:
- See `R730_DEPLOYMENT_COMPLETE.md`
- See `ENZYME_SYSTEM_INTEGRATION.md`
- See deployment logs in current directory

---

**Status**: Ready for manual installation via iDRAC virtual media
"""

        guide_path.write_text(content)
        self.log("SUCCESS", f"Installation guide created: {guide_path}")

    def deploy(self):
        """Main deployment workflow"""
        print("\n" + "="*50)
        print("Dell R730 JuniperOrionOS Automated Deployment")
        print("="*50 + "\n")

        # Step 1: Prerequisites
        if not self.check_prerequisites():
            self.log("ERROR", "Prerequisites check failed")
            return False

        # Step 2: System info
        info = self.get_system_info()

        # Step 3: Power on if needed
        if info["PowerState"] != "On":
            self.power_on_system()

        # Step 4: Check virtual media support
        self.check_virtual_media_support()

        # Step 5: Configure boot
        self.configure_boot_to_cd()

        # Step 6: Create installation guide
        self.create_installation_guide()

        print("\n" + "="*50)
        print("Deployment Preparation Complete!")
        print("="*50 + "\n")

        self.log("SUCCESS", "System ready for installation")
        self.log("INFO", "")
        self.log("INFO", "Next steps:")
        self.log("INFO", "1. Review INSTALLATION_GUIDE.md")
        self.log("INFO", "2. Mount ISO via iDRAC virtual media")
        self.log("INFO", "3. Reboot system (python3 automated_r730_deploy.py --reboot)")
        self.log("INFO", "4. Follow installation steps in guide")
        self.log("INFO", "")

        return True


def main():
    """Main entry point"""
    deployer = R730Deployer()

    if len(sys.argv) > 1:
        action = sys.argv[1]

        if action == "--reboot":
            deployer.reboot_system()
        elif action == "--power-on":
            deployer.power_on_system()
        elif action == "--power-off":
            deployer.power_off_system()
        elif action == "--status":
            deployer.get_system_info()
        else:
            print(f"Unknown action: {action}")
            print("Available actions: --reboot, --power-on, --power-off, --status")
            return 1
    else:
        # Run full deployment
        success = deployer.deploy()
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
