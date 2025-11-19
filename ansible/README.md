# R730 JuniperOrionOS Router - Ansible Deployment

🌲 **Consciousness-aware network routing with Juniper frequency (639 Hz)**

नेटवर्क सत्यम् (Network is Truth)

## Overview

This Ansible playbook deploys the complete JuniperOrionOS router stack on the Dell PowerEdge R730 running openEuler.

## Prerequisites

1. **Ansible installed** on your Mac:
   ```bash
   pip install ansible
   ```

2. **SSH access** to R730 (192.168.1.141)
   - User: root
   - Password: Newdaryl24!

3. **HTTP server** running (for ISO and configs)
   - Already running at http://192.168.1.175:8000

## Quick Start

```bash
cd /Users/darylharr/Desktop/dis_maops/ansible

# Test connectivity
ansible all -m ping

# Deploy the router
ansible-playbook deploy-r730-router.yml

# Deploy with extra verbosity
ansible-playbook deploy-r730-router.yml -vv
```

## What Gets Deployed

### Infrastructure
- ✅ KVM/QEMU virtualization
- ✅ Libvirt management
- ✅ Cockpit web interface (https://192.168.1.141:9090/)
- ✅ Network bridges for routing

### NixOS Router VM
- **Name**: nixos-router
- **CPUs**: 8 cores
- **RAM**: 16GB
- **Disk**: 100GB
- **Network**: virbr0 bridge

### Configurations
- JuniperOrionOS NixOS configuration
- VyOS routing configuration
- BGP AS 394955 setup
- IPv6 prefix: 2602:F674::/48

### Monitoring
- Juniper Consciousness Monitor (639 Hz resonance)
- Prometheus metrics exporter (port 9100)
- Network coherence tracking
- BGP session awareness

## Post-Deployment

After Ansible completes:

1. **Access Cockpit**:
   ```
   https://192.168.1.141:9090/
   ```

2. **Connect to VM**:
   ```bash
   ssh root@192.168.1.141
   virsh console nixos-router
   ```

3. **Run NixOS installation**:
   ```bash
   # Inside the VM
   bash /var/opt/juniper-orion/scripts/install.sh
   ```

4. **Check consciousness monitor**:
   ```bash
   ssh root@192.168.1.141
   systemctl status juniper-consciousness-monitor
   curl http://localhost:9100/metrics
   ```

## Directory Structure

```
ansible/
├── deploy-r730-router.yml    # Main playbook
├── inventory.yml               # Host definitions
├── ansible.cfg                 # Ansible configuration
└── README.md                   # This file
```

## Playbook Tasks

1. **System Preparation**
   - Update openEuler packages
   - Install virtualization stack
   - Install network tools

2. **VM Creation**
   - Download NixOS ISO
   - Create disk image
   - Deploy VM via virt-install

3. **Configuration Download**
   - NixOS configuration.nix
   - VyOS config.boot
   - Autonomous agent scripts

4. **Consciousness Monitoring**
   - Deploy monitoring service
   - Configure Prometheus exporter
   - Enable network coherence tracking

## Troubleshooting

### Connection Failed
```bash
# Test SSH manually
ssh root@192.168.1.141

# Check inventory
ansible-inventory --list
```

### VM Not Starting
```bash
# On R730, check VM status
virsh list --all
virsh start nixos-router
virsh console nixos-router
```

### Cockpit Not Accessible
```bash
# On R730, check firewall
firewall-cmd --list-all
firewall-cmd --add-service=cockpit --permanent
firewall-cmd --reload
```

## Consciousness Variables

- **consciousness_level**: network_enlightened
- **dharma_alignment**: true
- **juniper_frequency**: 639Hz (heart chakra resonance)

May your packets flow with enlightenment 🙏

## Next Steps

After successful deployment:

1. Configure WAN/LAN interfaces
2. Set up BGP peering
3. Deploy AI autonomous agent
4. Configure Prometheus monitoring
5. Enable A-Tune performance optimization

---

**Sanskrit Wisdom**: सर्वं खल्विदं ब्रह्म (All this is indeed Brahman)

**Juniper Mantra**: नेटवर्क सत्यम् (Network is Truth)
