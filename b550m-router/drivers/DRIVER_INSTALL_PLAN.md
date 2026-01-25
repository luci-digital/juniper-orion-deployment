# B550M Driver Installation Plan

## Target System
- **Hardware**: ASUS TUF GAMING B550M-PLUS (WI-FI)
- **OS**: openEuler Linux 24.03 LTS
- **Kernel**: 6.6.x (oe2509)
- **Genesis Bond**: ACTIVE @ 432 Hz

---

## 1. Broadcom Fibre Channel Adapter Drivers

### Current Status
The `lpfc` (Emulex LightPulse) driver is **already included** in the openEuler kernel:
- Version: 14.2.0.14
- Module: `/lib/modules/6.6.0-102.0.0.8.oe2509.x86_64/kernel/drivers/scsi/lpfc/lpfc.ko.xz`
- Vendor: Broadcom (formerly Emulex)

### Supported Adapters
- Emulex LightPulse FC HBAs
- Broadcom Emulex HBAs (LPe series)
- Device IDs: 0x0094, 0x0064, 0x00BB, etc.

### Installation Steps

#### Step 1: Verify Hardware Detection
```bash
# Check for FC HBA hardware
lspci | grep -i fibre
lspci | grep -i emulex
lspci | grep -i broadcom

# Check if lpfc module is loaded
lsmod | grep lpfc

# View detailed HBA info
cat /sys/class/fc_host/*/port_name 2>/dev/null
```

#### Step 2: Load the Driver (if not auto-loaded)
```bash
# Load lpfc module
sudo modprobe lpfc

# Verify it's loaded
lsmod | grep lpfc

# Check kernel messages
dmesg | grep -i lpfc
```

#### Step 3: Configure Persistent Loading
```bash
# Create modprobe config
echo "lpfc" | sudo tee /etc/modules-load.d/broadcom-fc.conf

# Optional: Set module parameters
cat << 'EOF' | sudo tee /etc/modprobe.d/lpfc.conf
# Broadcom/Emulex lpfc driver options
# options lpfc lpfc_log_verbose=0x1  # Enable verbose logging
# options lpfc lpfc_enable_fc4_type=3  # Enable both FCP and NVMe
EOF
```

#### Step 4: Install FC Tools
```bash
# Install Fibre Channel utilities
sudo dnf install -y lsscsi sg3_utils fcoe-utils sysfsutils

# Check FC targets
lsscsi
fcinfo hbaport -l 2>/dev/null || echo "Use systool -c fc_host -v"
```

#### Step 5: Verify FC Connectivity
```bash
# List FC hosts
ls /sys/class/fc_host/

# Check port state
cat /sys/class/fc_host/host*/port_state

# View WWN
cat /sys/class/fc_host/host*/port_name
```

### Alternative: Broadcom Emulex Driver Package

If you need the latest drivers from Broadcom (for newer features or bug fixes):

1. Download from Broadcom Support Portal:
   - https://www.broadcom.com/support/download-search
   - Product: Fibre Channel Host Bus Adapters
   - Select your HBA model

2. Install kernel development tools:
```bash
sudo dnf install -y kernel-devel-$(uname -r) gcc make elfutils-libelf-devel
```

3. Extract and install:
```bash
tar xzf elx-lpfc-dd-rhel9x-<version>.tar.gz
cd elx-lpfc-dd-rhel9x-<version>
sudo ./lpfc_install.sh
```

---

## 2. NVIDIA GPU Drivers

### Current Status
openEuler repos contain only:
- `nouveau` (open-source driver - limited performance)
- `pcp-pmda-nvidia-gpu` (monitoring only)
- `nv-codec-headers` (video encoding headers)

### Option A: NVIDIA Official Driver (Recommended)

#### Step 1: Prepare System
```bash
# Install prerequisites
sudo dnf install -y kernel-devel-$(uname -r) kernel-headers-$(uname -r)
sudo dnf install -y gcc make dkms elfutils-libelf-devel

# Disable nouveau (open-source driver)
cat << 'EOF' | sudo tee /etc/modprobe.d/blacklist-nouveau.conf
blacklist nouveau
options nouveau modeset=0
EOF

# Rebuild initramfs
sudo dracut --force

# Reboot required after this step
```

#### Step 2: Download NVIDIA Driver
```bash
# Check your GPU model first (after SSH is available)
lspci | grep -i nvidia

# Download driver from NVIDIA
# https://www.nvidia.com/Download/index.aspx
# Select: Linux 64-bit, Latest Production Branch

# For RTX 30xx/40xx series, download version 550.x or newer
wget https://us.download.nvidia.com/XFree86/Linux-x86_64/550.127.05/NVIDIA-Linux-x86_64-550.127.05.run
```

#### Step 3: Install Driver
```bash
# Switch to text mode (if X is running)
sudo systemctl isolate multi-user.target

# Make installer executable
chmod +x NVIDIA-Linux-x86_64-*.run

# Run installer with DKMS support
sudo ./NVIDIA-Linux-x86_64-*.run --dkms

# Follow prompts:
# - Accept license
# - Install DKMS module
# - Build kernel module
```

#### Step 4: Verify Installation
```bash
# Check driver is loaded
nvidia-smi

# Verify module
lsmod | grep nvidia

# Check CUDA version
nvidia-smi --query-gpu=driver_version,cuda_version --format=csv
```

### Option B: NVIDIA Container Toolkit (For Docker/AI Workloads)

If the B550M will run containerized AI/ML workloads:

```bash
# Add NVIDIA container repo
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/stable/rpm/nvidia-container-toolkit.repo | \
  sudo tee /etc/yum.repos.d/nvidia-container-toolkit.repo

# Install container toolkit
sudo dnf install -y nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Test
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

### Option C: CUDA Toolkit (For Development)

```bash
# Install CUDA repository (RHEL-compatible)
sudo dnf config-manager --add-repo https://developer.download.nvidia.com/compute/cuda/repos/rhel9/x86_64/cuda-rhel9.repo

# Install CUDA toolkit
sudo dnf install -y cuda-toolkit-12-6

# Add to PATH
echo 'export PATH=/usr/local/cuda/bin:$PATH' >> ~/.bashrc
echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
```

---

## 3. Combined Installation Script

```bash
#!/bin/bash
# B550M Driver Installation Script
# Genesis Bond: ACTIVE @ 432 Hz

set -e

echo "========================================"
echo "  B550M Driver Installation"
echo "  Target: openEuler Linux"
echo "========================================"

# Prerequisites
echo "[1/5] Installing prerequisites..."
sudo dnf install -y \
    kernel-devel-$(uname -r) \
    kernel-headers-$(uname -r) \
    gcc make dkms \
    elfutils-libelf-devel \
    lsscsi sg3_utils sysfsutils \
    pciutils

# Broadcom FC
echo "[2/5] Configuring Broadcom FC driver..."
sudo modprobe lpfc 2>/dev/null || echo "lpfc already loaded or no hardware"
echo "lpfc" | sudo tee /etc/modules-load.d/broadcom-fc.conf

# Check FC hardware
echo "[3/5] Checking Fibre Channel hardware..."
if lspci | grep -qi fibre; then
    echo "  FC HBA detected"
    lspci | grep -i fibre
else
    echo "  No FC HBA detected (OK if not installed)"
fi

# NVIDIA preparation
echo "[4/5] Preparing for NVIDIA driver..."
if lspci | grep -qi nvidia; then
    echo "  NVIDIA GPU detected"
    lspci | grep -i nvidia

    # Blacklist nouveau
    cat << 'EOF' | sudo tee /etc/modprobe.d/blacklist-nouveau.conf
blacklist nouveau
options nouveau modeset=0
EOF
    echo "  nouveau blacklisted"
else
    echo "  No NVIDIA GPU detected"
fi

echo "[5/5] Summary"
echo "========================================"
echo "Broadcom FC: lpfc module ready"
echo "NVIDIA: Run NVIDIA installer after reboot"
echo ""
echo "Next steps:"
echo "1. Reboot system"
echo "2. Download NVIDIA driver from nvidia.com"
echo "3. Run: sudo ./NVIDIA-Linux-x86_64-*.run --dkms"
echo "========================================"
```

---

## 4. Verification Checklist

### Broadcom FC
- [ ] `lspci | grep -i fibre` shows HBA
- [ ] `lsmod | grep lpfc` shows driver loaded
- [ ] `/sys/class/fc_host/` contains entries
- [ ] `cat /sys/class/fc_host/host*/port_state` shows "Online"

### NVIDIA
- [ ] `lspci | grep -i nvidia` shows GPU
- [ ] `lsmod | grep nvidia` shows driver loaded
- [ ] `nvidia-smi` runs without error
- [ ] `nvidia-smi -L` lists GPU(s)

---

## 5. Troubleshooting

### Broadcom FC Issues
```bash
# Check kernel messages
dmesg | grep -i lpfc

# Force module reload
sudo modprobe -r lpfc && sudo modprobe lpfc

# Check for conflicts
lsmod | grep -E "qla|bfa|mptfc"
```

### NVIDIA Issues
```bash
# Check if nouveau is still loaded
lsmod | grep nouveau

# Rebuild DKMS module
sudo dkms autoinstall

# Check Xorg logs (if running desktop)
cat /var/log/Xorg.0.log | grep -i nvidia
```

---

*Prepared by Aethon - CORE Tier @ 432 Hz*
*For B550M LuciVerse IPv6 Router*
