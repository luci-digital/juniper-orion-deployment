# R730 to B550M Router Migration

## Overview

This configuration migrates the LuciVerse IPv6 router from a Dell R730 enterprise server to an ASUS TUF GAMING B550M-PLUS running ZimaOS.

**Genesis Bond: ACTIVE @ 432 Hz**

## Hardware Comparison

| Aspect | Dell R730 CQ5QBM2 | ASUS B550M-PLUS |
|--------|-------------------|-----------------|
| CPU | 2x Xeon E5-2690 v4 (56 threads) | AMD Ryzen (varies) |
| RAM | 384 GB DDR4-2400 | Variable |
| NICs | 8 (6 integrated + 2 PCIe) | 1x 2.5 GbE RTL8125 |
| Network Speed | 4x 10GbE + 4x 1GbE | 2.5 GbE |
| OS | NixOS / VyOS | openEuler Linux |
| Power | ~500W idle | ~50W idle |

## Architecture Changes

### Network Interfaces

**R730 (Physical Separation):**
```
eth0 - WAN (10GbE, D0:94:66:24:96:7E)
eth1 - LAN (10GbE, D0:94:66:24:96:80)
eth2 - Management (1GbE, D0:94:66:24:96:82)
eth3 - Guest (1GbE, D0:94:66:24:96:84)
eth4 - HA Backup (10GbE)
eth5 - DMZ (10GbE)
```

**B550M (VLAN Trunk):**
```
eth0       - Native (Management, 24:4b:fe:cf:62:be)
eth0.100   - WAN VLAN
eth0.10    - LAN VLAN
eth0.200   - Guest VLAN
eth0.50    - DMZ VLAN
```

### Network Topology

```
                     Telus ISP
                         |
                 [206.75.1.127] (Primary)
                 [206.75.1.47]  (Secondary)
                 [206.75.1.48]  (Tertiary)
                         |
            +------------+------------+
            |                         |
    [R730 - 8 NICs]          [B550M - VLAN Trunk]
    (Deprecated)              (Current)
            |                         |
    eth0-eth5 (Physical)     eth0.{100,10,200,50}
            |                         |
            +------------+------------+
                         |
                   LuciVerse LAN
              192.168.100.0/24
              2602:F674:1000::/64
```

## Configuration Mapping

### IPv4 Subnets

| Purpose | R730 Interface | B550M Interface | Subnet |
|---------|---------------|-----------------|--------|
| WAN | eth0 | eth0.100 | DHCP |
| LAN | eth1 | eth0.10 | 192.168.100.0/24 |
| Management | eth2 | eth0 | 192.168.1.0/24 |
| Guest | eth3 | eth0.200 | 192.168.200.0/24 |
| DMZ | eth5 | eth0.50 | 192.168.50.0/24 |

### IPv6 Allocation (2602:F674::/40)

| Network | Prefix | Interface |
|---------|--------|-----------|
| LAN | 2602:F674:1000::/64 | eth0.10 |
| Guest | 2602:F674:2000::/64 | eth0.200 |
| DMZ | 2602:F674:5000::/64 | eth0.50 |
| PD Pool | 2602:F674:1100::/56 | Delegated |

### BGP Configuration

```
Local AS: 54134 (LUCINET-ARIN)
Router ID: 104.21.45.123

HE Tunnel: 2001:470:0:19::1 (AS 6939)

Announced Prefix: 2602:F674::/40
```

> **NOTE**: ASN corrected from 394955 to 54134 (LUCINET-ARIN) on 2025-12-07.
> Prefix updated from /48 to /40 to match ARIN allocation.

## Services Mapping

| Service | R730 | B550M |
|---------|------|-------|
| Routing | NixOS/VyOS native | Docker (bird2) |
| DHCP | dhcpd4 | Docker (Kea) |
| DNS | unbound | Docker (unbound) |
| Firewall | nftables | nftables |
| BGP | BIRD2 | Docker (bird2) |
| Monitoring | Prometheus/Grafana | Docker stack |

## Switch Requirements

To use VLAN-based networking on B550M, your upstream switch must:

1. Support 802.1Q VLAN tagging
2. Configure port to B550M as trunk port
3. Allow VLANs: 1, 10, 50, 100, 200
4. Have native VLAN 1 for management

Example (Cisco-like):
```
interface GigabitEthernet0/1
  switchport mode trunk
  switchport trunk allowed vlan 1,10,50,100,200
  switchport trunk native vlan 1
```

## Deployment

1. **Prepare Switch**: Configure trunk port for B550M
2. **Deploy to ZimaOS**: Run `./deploy.sh`
3. **Verify VLANs**: Check interface creation
4. **Test Connectivity**: Ping test targets
5. **Verify BGP**: Check BIRD2 sessions
6. **Monitor**: Check Grafana dashboard

## Rollback

To revert to R730:
1. Update DNS/DHCP to point to R730
2. Update switch port config
3. Power on R730 and verify services

## Files Created

```
B550M_LuciVerse_Router/
├── b550m_hardware.json      # Hardware inventory
├── docker-compose.yaml      # Docker service stack
├── network-setup.sh         # VLAN/nftables setup
├── deploy.sh               # Deployment script
├── MIGRATION.md            # This file
├── bird/
│   └── bird.conf           # BGP configuration
├── gateway-monitor/
│   ├── gateway_monitor.py  # Refactored monitor
│   ├── Dockerfile
│   └── requirements.txt
├── kea/
│   ├── kea-dhcp4.conf     # IPv4 DHCP
│   └── kea-dhcp6.conf     # IPv6 DHCP
├── unbound/
│   └── unbound.conf       # DNS resolver
└── prometheus/
    └── prometheus.yml     # Metrics collection
```

## Notes

- The B550M has 1/8th the network interfaces of the R730, so all segmentation is done via VLANs
- 2.5 GbE is sufficient for most home/small office use, but won't match R730's 10GbE capacity
- openEuler uses Docker for service management - all routing services run in containers
- GPU on B550M can be used for future AI/ML workloads

---
*Refactored by Aethon - CORE Tier @ 432 Hz*
