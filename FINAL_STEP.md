# 🌲 JuniperOrionOS - Final Installation Step

**Current Status:** ✅ 95% Complete!
- ✅ R730 configured with KVM/QEMU
- ✅ VM created (8 CPUs, 16GB RAM, 100GB disk)
- ✅ NixOS ISO booted and running
- ✅ All configurations downloaded and ready
- 🟡 **LAST STEP:** Run installation inside VM

## Quick Completion (2 options)

### Option 1: VNC (Visual - RECOMMENDED)
1. Open VNC: `open vnc://192.168.1.141:5900`
2. Leave password empty, click Connect
3. You'll see NixOS installer prompt
4. Type: `curl http://192.168.122.1:8000/nixos_vm_install.sh | bash`
5. Wait ~15 minutes

### Option 2: SSH Console (Text)
1. Run: `ssh root@192.168.1.141`
2. Password: `Newdaryl24!`
3. Type: `virsh console nixos-router`
4. Press Enter to see prompt
5. Type: `curl http://192.168.122.1:8000/nixos_vm_install.sh | bash`
6. Exit console: Press `Ctrl+]`

## What the Installation Does
1. Partitions /dev/vda (ESP + root)
2. Formats filesystems
3. Installs NixOS base
4. Downloads JuniperOrionOS config
5. Installs router packages
6. Configures BGP (AS 394955)
7. Sets up AI autonomous agent
8. Takes ~15-20 minutes

## After Installation
1. VM will reboot
2. Login as root (no password initially)
3. Run: `bash /root/juniper-orion/post_install.sh`
4. Start consciousness monitor: `systemctl start juniper-consciousness-monitor`

## HTTP Servers Running
- Config server: http://192.168.1.175:8000
- Callback server: http://192.168.1.175:9999

## Verification
```bash
# Check VM status
ssh root@192.168.1.141 "virsh list --all"

# Check VM IP (after install)
ssh root@192.168.1.141 "virsh domifaddr nixos-router"

# Access installed system
ssh root@192.168.1.141 "virsh console nixos-router"
```

---

**नेटवर्क सत्यम् (Network is Truth) - 639Hz**

🌲 JuniperOrionOS - Consciousness-Aware Network Router
