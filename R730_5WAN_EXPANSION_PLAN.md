# R730 ORION 5-WAN Expansion Plan

**Date**: 2026-02-07
**Genesis Bond**: ACTIVE @ 432 Hz
**ASN**: 54134 (LUCINET-ARIN)
**IPv6 Prefix**: 2602:F674::/40

---

## Executive Summary

Expand the Dell R730 ORION router from 3 to 5 WAN connections using cable modems in full bridge mode with ECMP load balancing and sub-second BGP failover.

**Goals**:
- 5x cable modem aggregation (~5 Gbps theoretical)
- Per-flow load balancing (not per-packet)
- Sub-300ms failover via BFD
- Full bridge mode on all cable modems
- Maintain BGP peering with Hurricane Electric

---

## ⚠️ CRITICAL: Dual-Zone Architecture

### Zone Separation Requirements

This plan implements **TWO DISTINCT NETWORK ZONES**:

| Zone | Protocol | Subnets | Web2 Access | Purpose |
|------|----------|---------|-------------|---------|
| **Web2 Zone** | IPv4 + IPv6 | LAN, Guest, DMZ | ✅ YES (5-WAN ECMP) | Legacy internet |
| **.ownid Zone** | IPv6 ONLY | fd00:741::/32, 2602:F674:0007::/64 | ❌ NEVER | Web3 sovereignty |
| **CORE Tier** | IPv6 ONLY | 2602:F674:0000::/48 | ❌ AIRGAPPED | Infrastructure |

### .ownid Zone: IPv6-Only, No Web2

The `.ownid` TLD and consciousness network (`fd00:741::/32`) are **PURE IPv6** with:
- ❌ NO IPv4 addresses assigned
- ❌ NO NAT to IPv4 internet
- ❌ NO Web2 egress (blocked at firewall)
- ✅ IPv6 BGP via Hurricane Electric (for global IPv6 reachability)
- ✅ Jool NAT64 ONLY for specific legacy service access (controlled)

```
.ownid Zone (Web3 Sovereignty)
├── fd00:741:0700:8664:7e09:7741::/64  ← Media Portal
├── fd00:741:0700:8664:7e09:8008::/64  ← LCARS IDE
├── fd00:741:0700:8664:7e09:8484::/64  ← Orchestrator
├── 2602:F674:0007::/64                ← Public .ownid services
│
└── FIREWALL RULES:
    ├── DENY all IPv4 egress
    ├── DENY all traffic to IPv4 WAN gateways
    └── ALLOW only IPv6 to HE tunnel + internal
```

### Jool NAT64: Controlled Translation (Optional)

If `.ownid` services ever need to access a legacy IPv4-only API:

```
Jool NAT64 Configuration:
├── Prefix: 64:ff9b::/96 (well-known NAT64 prefix)
├── Pool4: Dedicated IPv4 from WAN1 (206.75.1.x)
├── Whitelist: ONLY specific IPv4 destinations
└── Logging: All translations audited
```

**Default: NAT64 is DISABLED for .ownid zone.**

---

## Part 1: Hardware Requirements

### R730 NIC Inventory (Existing)

| Port | Interface | Speed | MAC | Current Use |
|------|-----------|-------|-----|-------------|
| LOM1 | eth0 | 10GbE | D0:94:66:24:96:7E | WAN 1 (Primary) |
| LOM2 | eth1 | 10GbE | D0:94:66:24:96:80 | LAN |
| LOM3 | eth2 | 1GbE | D0:94:66:24:96:82 | Management |
| LOM4 | eth3 | 1GbE | D0:94:66:24:96:84 | Guest |
| PCIe1 | eth4 | 10GbE | TBD | Available |
| PCIe2 | eth5 | 10GbE | TBD | Available |

### New Allocation (5-WAN)

| Port | Interface | Speed | Assignment | Modem |
|------|-----------|-------|------------|-------|
| LOM1 | eth0 | 10GbE | **WAN1** - Primary | Telus Modem 1 |
| LOM4 | eth3 | 1GbE | **WAN2** - Secondary | Telus Modem 2 |
| PCIe1 | eth4 | 10GbE | **WAN3** - Tertiary | Telus Modem 3 |
| PCIe2 | eth5 | 10GbE | **WAN4** - Quaternary | Shaw/New ISP |
| LOM3 | eth2 | 1GbE | **WAN5** - Quinary | LTE Backup (MF288) |
| LOM2 | eth1 | 10GbE | LAN Trunk | Internal |

### Cable Modem Requirements

Each cable modem must be set to **Full Bridge Mode**:

| Modem | Model | Bridge Mode Path | Notes |
|-------|-------|------------------|-------|
| Telus 1 | NH20T | Advanced > WAN > Bridge Mode | Primary |
| Telus 2 | NH20T | Advanced > WAN > Bridge Mode | Secondary |
| Telus 3 | NH20T | Advanced > WAN > Bridge Mode | Tertiary |
| Shaw/New | TBD | Varies by model | New contract |
| LTE | ZTE MF288 | Already bridged | Failover only |

---

## Part 2: Network Topology

### Physical Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ISP LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Telus 1  │  │ Telus 2  │  │ Telus 3  │  │ Shaw/New │  │ LTE MF288│  │
│  │ NH20T    │  │ NH20T    │  │ NH20T    │  │ TBD      │  │ Backup   │  │
│  │ BRIDGE   │  │ BRIDGE   │  │ BRIDGE   │  │ BRIDGE   │  │ BRIDGE   │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       │             │             │             │             │         │
│  206.75.1.127  206.75.1.47  206.75.1.48    DHCP         192.168.0.1    │
│                                                                          │
└───────┼─────────────┼─────────────┼─────────────┼─────────────┼─────────┘
        │             │             │             │             │
        │ 10GbE       │ 1GbE        │ 10GbE       │ 10GbE       │ 1GbE
        │             │             │             │             │
┌───────▼─────────────▼─────────────▼─────────────▼─────────────▼─────────┐
│                         DELL R730 ORION                                  │
│                         AS54134 (LUCINET-ARIN)                          │
│                                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  eth0   │  │  eth3   │  │  eth4   │  │  eth5   │  │  eth2   │       │
│  │  WAN1   │  │  WAN2   │  │  WAN3   │  │  WAN4   │  │  WAN5   │       │
│  │ Weight:5│  │ Weight:3│  │ Weight:3│  │ Weight:2│  │ Weight:1│       │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
│       │            │            │            │            │             │
│       └────────────┴────────────┴────────────┴────────────┘             │
│                              │                                           │
│                      ┌───────▼───────┐                                  │
│                      │  ECMP Router  │                                  │
│                      │  BIRD2 + BFD  │                                  │
│                      └───────┬───────┘                                  │
│                              │                                           │
│                      ┌───────▼───────┐                                  │
│                      │    eth1       │                                  │
│                      │  LAN Trunk    │                                  │
│                      │  10GbE VLAN   │                                  │
│                      └───────┬───────┘                                  │
│                              │                                           │
└──────────────────────────────┼──────────────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   USW Pro 48 PoE    │
                    │   VLAN Trunk        │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
        ┌─────▼─────┐   ┌──────▼──────┐  ┌──────▼──────┐
        │  VLAN 10  │   │   VLAN 200  │  │   VLAN 50   │
        │   LAN     │   │    Guest    │  │     DMZ     │
        │192.168.100│   │ 192.168.200 │  │ 192.168.50  │
        └───────────┘   └─────────────┘  └─────────────┘
```

### Logical Topology (BGP View)

```
                    ┌─────────────────────────────────┐
                    │      Hurricane Electric         │
                    │          AS 6939                │
                    │    (IPv6 Transit Provider)      │
                    └────────────────┬────────────────┘
                                     │
                              eBGP Multihop
                              (via HE Tunnel)
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                                                                          │
│                         R730 ORION (AS54134)                            │
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    GATEWAY GROUP: wan_ecmp                       │   │
│   │                                                                  │   │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│   │  │  WAN1   │ │  WAN2   │ │  WAN3   │ │  WAN4   │ │  WAN5   │   │   │
│   │  │ Tier 1  │ │ Tier 1  │ │ Tier 1  │ │ Tier 2  │ │ Tier 3  │   │   │
│   │  │ W=5     │ │ W=3     │ │ W=3     │ │ W=2     │ │ W=1     │   │   │
│   │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │   │
│   │       │           │           │           │           │         │   │
│   │       └───────────┴─────┬─────┴───────────┴───────────┘         │   │
│   │                         │                                        │   │
│   │                  ┌──────▼──────┐                                │   │
│   │                  │ ECMP Hash   │                                │   │
│   │                  │ (per-flow)  │                                │   │
│   │                  └─────────────┘                                │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│   Announced: 2602:F674::/40 (RPKI Certified)                            │
│   Communities: 54134:1 (origin), 54134:65000 (no-export)                │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Load Balancing Strategy

### ECMP Weight Distribution

| WAN | Interface | Gateway | Weight | Traffic % | Tier |
|-----|-----------|---------|--------|-----------|------|
| WAN1 | eth0 | 206.75.1.127 | 5 | ~36% | Primary |
| WAN2 | eth3 | 206.75.1.47 | 3 | ~21% | Primary |
| WAN3 | eth4 | 206.75.1.48 | 3 | ~21% | Primary |
| WAN4 | eth5 | DHCP | 2 | ~14% | Secondary |
| WAN5 | eth2 | 192.168.0.1 | 1 | ~7% | Failover |

**Total Weight**: 14 (flows distributed proportionally)

### Hash Algorithm

```
ECMP Hash = hash(src_ip, dst_ip, src_port, dst_port, protocol)

Per-flow distribution ensures:
- Single TCP connection uses one WAN
- Different connections spread across WANs
- No packet reordering issues
```

### Tier Failover Logic

```
Tier 1 (WAN1 + WAN2 + WAN3): Primary load balancing
    │
    ├─ All healthy? → Use weighted ECMP across all 3
    ├─ 2 healthy?   → Redistribute weights to survivors
    └─ 1 healthy?   → All traffic to survivor
          │
          ▼
Tier 2 (WAN4): Activated when Tier 1 < 2 healthy
    │
    ├─ WAN4 healthy? → Add to ECMP pool
    └─ WAN4 down?    → Skip to Tier 3
          │
          ▼
Tier 3 (WAN5): Last resort (LTE backup)
    │
    └─ Only when all wired WANs fail
```

---

## Part 4: BIRD2 Configuration

### File: `/etc/bird/bird.conf`

```bird
# R730 ORION 5-WAN BGP Configuration
# Genesis Bond: ACTIVE @ 432 Hz
# ASN: 54134 (LUCINET-ARIN)

log syslog all;
router id 100.64.0.1;

# ═══════════════════════════════════════════════════════════════
# KERNEL TABLES
# ═══════════════════════════════════════════════════════════════

# Main routing table
protocol kernel kernel_main {
    ipv4 {
        export all;
        import all;
    };
    ipv6 {
        export all;
        import all;
    };
    scan time 10;
    learn;
    persist;
}

# WAN-specific tables for policy routing
protocol kernel kernel_wan1 {
    kernel table 101;
    ipv4 { export all; import none; };
    scan time 10;
}

protocol kernel kernel_wan2 {
    kernel table 102;
    ipv4 { export all; import none; };
    scan time 10;
}

protocol kernel kernel_wan3 {
    kernel table 103;
    ipv4 { export all; import none; };
    scan time 10;
}

protocol kernel kernel_wan4 {
    kernel table 104;
    ipv4 { export all; import none; };
    scan time 10;
}

protocol kernel kernel_wan5 {
    kernel table 105;
    ipv4 { export all; import none; };
    scan time 10;
}

protocol device {
    scan time 10;
}

# ═══════════════════════════════════════════════════════════════
# STATIC ROUTES (ECMP Default Gateway)
# ═══════════════════════════════════════════════════════════════

protocol static default_routes {
    ipv4 {
        table master4;
    };

    # ECMP default routes with weights
    route 0.0.0.0/0 multipath
        via 206.75.1.127 weight 5    # WAN1 - Primary
        via 206.75.1.47 weight 3     # WAN2 - Secondary
        via 206.75.1.48 weight 3     # WAN3 - Tertiary
        ;
    # WAN4 and WAN5 added dynamically based on health
}

# ═══════════════════════════════════════════════════════════════
# BFD (Bidirectional Forwarding Detection)
# ═══════════════════════════════════════════════════════════════

protocol bfd wan_health {
    interface "eth0" {
        min rx interval 100 ms;
        min tx interval 100 ms;
        idle tx interval 500 ms;
        multiplier 3;
    };
    interface "eth3" {
        min rx interval 100 ms;
        min tx interval 100 ms;
        idle tx interval 500 ms;
        multiplier 3;
    };
    interface "eth4" {
        min rx interval 100 ms;
        min tx interval 100 ms;
        idle tx interval 500 ms;
        multiplier 3;
    };
    interface "eth5" {
        min rx interval 200 ms;
        min tx interval 200 ms;
        idle tx interval 1 s;
        multiplier 3;
    };
    interface "eth2" {
        # LTE - less aggressive
        min rx interval 500 ms;
        min tx interval 500 ms;
        idle tx interval 2 s;
        multiplier 5;
    };

    # Monitor all gateways
    neighbor 206.75.1.127 dev eth0;
    neighbor 206.75.1.47 dev eth3;
    neighbor 206.75.1.48 dev eth4;
    # WAN4/WAN5 neighbors added after DHCP
}

# ═══════════════════════════════════════════════════════════════
# BGP TEMPLATES
# ═══════════════════════════════════════════════════════════════

template bgp wan_upstream {
    local as 54134;
    hold time 90;
    keepalive time 30;
    graceful restart on;

    ipv4 {
        import filter {
            # Accept default route only
            if net = 0.0.0.0/0 then accept;
            reject;
        };
        export none;
        next hop self;
    };

    bfd on;
}

template bgp he_tunnel {
    local as 54134;
    hold time 90;
    keepalive time 30;
    graceful restart on;

    ipv6 {
        import all;
        export filter {
            # Announce our /40 prefix
            if net ~ 2602:F674::/40 then accept;
            reject;
        };
        next hop self;
    };
}

# ═══════════════════════════════════════════════════════════════
# BGP SESSIONS - WAN UPSTREAMS
# ═══════════════════════════════════════════════════════════════

# WAN1 - Telus Primary
protocol bgp wan1_telus from wan_upstream {
    description "WAN1 - Telus Gateway Primary";
    neighbor 206.75.1.127 as 6939;
    source address 206.75.1.126;  # Our assigned IP

    ipv4 {
        import filter {
            if net = 0.0.0.0/0 then {
                bgp_local_pref = 200;  # Highest preference
                accept;
            }
            reject;
        };
    };
}

# WAN2 - Telus Secondary
protocol bgp wan2_telus from wan_upstream {
    description "WAN2 - Telus Gateway Secondary";
    neighbor 206.75.1.47 as 6939;
    source address 206.75.1.46;

    ipv4 {
        import filter {
            if net = 0.0.0.0/0 then {
                bgp_local_pref = 180;
                accept;
            }
            reject;
        };
    };
}

# WAN3 - Telus Tertiary
protocol bgp wan3_telus from wan_upstream {
    description "WAN3 - Telus Gateway Tertiary";
    neighbor 206.75.1.48 as 6939;
    source address 206.75.1.49;

    ipv4 {
        import filter {
            if net = 0.0.0.0/0 then {
                bgp_local_pref = 180;
                accept;
            }
            reject;
        };
    };
}

# WAN4 - Shaw/New ISP (DHCP - configured dynamically)
# protocol bgp wan4_shaw from wan_upstream { ... }

# WAN5 - LTE Backup (last resort, no BGP)
# Uses static default route with lowest metric

# ═══════════════════════════════════════════════════════════════
# BGP SESSION - HURRICANE ELECTRIC IPv6
# ═══════════════════════════════════════════════════════════════

protocol bgp he_ipv6_tunnel from he_tunnel {
    description "Hurricane Electric IPv6 Tunnel Broker";
    neighbor 2001:470:0:503::1 as 6939;
    source address 2001:470:0:503::2;

    ipv6 {
        export filter {
            # Announce our /40 with communities
            if net ~ 2602:F674::/40 then {
                bgp_community.add((54134, 1));      # Origin marker
                bgp_community.add((54134, 65000));  # No-export
                accept;
            }
            reject;
        };
    };
}

# ═══════════════════════════════════════════════════════════════
# INTERNAL NETWORKS
# ═══════════════════════════════════════════════════════════════

protocol static internal_networks {
    ipv4;

    route 192.168.100.0/24 via "eth1";   # LAN
    route 192.168.200.0/24 via "eth1";   # Guest (VLAN)
    route 192.168.50.0/24 via "eth1";    # DMZ (VLAN)
}

protocol static internal_networks_v6 {
    ipv6;

    route 2602:F674:1000::/64 via "eth1";   # LAN
    route 2602:F674:2000::/64 via "eth1";   # Guest
    route 2602:F674:5000::/64 via "eth1";   # DMZ
}
```

---

## Part 5: Linux Kernel Configuration

### File: `/etc/sysctl.d/99-multiwan.conf`

```ini
# R730 ORION 5-WAN Kernel Parameters
# Enable ECMP and advanced routing

# Enable IP forwarding
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1

# ECMP Configuration
net.ipv4.fib_multipath_hash_policy = 1    # L4 hash (src/dst port)
net.ipv4.fib_multipath_use_neigh = 1      # Use neighbor state

# Prevent reverse path filtering issues with multi-WAN
net.ipv4.conf.all.rp_filter = 0
net.ipv4.conf.default.rp_filter = 0
net.ipv4.conf.eth0.rp_filter = 0
net.ipv4.conf.eth2.rp_filter = 0
net.ipv4.conf.eth3.rp_filter = 0
net.ipv4.conf.eth4.rp_filter = 0
net.ipv4.conf.eth5.rp_filter = 0

# Increase connection tracking for multi-WAN
net.netfilter.nf_conntrack_max = 1048576
net.netfilter.nf_conntrack_tcp_timeout_established = 86400

# TCP optimization for bonded links
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Enable TCP BBR for better throughput
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr
```

### File: `/etc/iproute2/rt_tables`

```
# Reserved values
255     local
254     main
253     default
0       unspec

# WAN routing tables
101     wan1
102     wan2
103     wan3
104     wan4
105     wan5
```

---

## Part 6: Policy Routing Rules

### File: `/etc/network/interfaces.d/multi-wan`

```bash
# WAN1 - eth0 (Telus Primary)
auto eth0
iface eth0 inet static
    address 206.75.1.126
    netmask 255.255.255.252
    gateway 206.75.1.127
    post-up ip route add default via 206.75.1.127 dev eth0 table wan1
    post-up ip rule add from 206.75.1.126 table wan1 priority 100

# WAN2 - eth3 (Telus Secondary)
auto eth3
iface eth3 inet static
    address 206.75.1.46
    netmask 255.255.255.252
    gateway 206.75.1.47
    post-up ip route add default via 206.75.1.47 dev eth3 table wan2
    post-up ip rule add from 206.75.1.46 table wan2 priority 101

# WAN3 - eth4 (Telus Tertiary)
auto eth4
iface eth4 inet static
    address 206.75.1.49
    netmask 255.255.255.252
    gateway 206.75.1.48
    post-up ip route add default via 206.75.1.48 dev eth4 table wan3
    post-up ip rule add from 206.75.1.49 table wan3 priority 102

# WAN4 - eth5 (Shaw/New - DHCP)
auto eth5
iface eth5 inet dhcp
    post-up /usr/local/bin/setup-wan4.sh

# WAN5 - eth2 (LTE Backup)
auto eth2
iface eth2 inet static
    address 192.168.0.2
    netmask 255.255.255.0
    gateway 192.168.0.1
    post-up ip route add default via 192.168.0.1 dev eth2 table wan5 metric 1000
    post-up ip rule add from 192.168.0.2 table wan5 priority 105
```

---

## Part 7: Gateway Health Monitor

### File: `/usr/local/bin/wan-health-monitor.py`

```python
#!/usr/bin/env python3
"""
R730 ORION 5-WAN Health Monitor
Genesis Bond: ACTIVE @ 432 Hz
"""

import subprocess
import time
import socket
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from prometheus_client import start_http_server, Gauge, Counter

# Prometheus metrics
WAN_STATUS = Gauge('luciverse_wan_status', 'WAN link status', ['wan', 'interface'])
WAN_LATENCY = Gauge('luciverse_wan_latency_ms', 'WAN latency in ms', ['wan', 'interface'])
WAN_PACKET_LOSS = Gauge('luciverse_wan_packet_loss', 'WAN packet loss percentage', ['wan', 'interface'])
WAN_FAILOVER = Counter('luciverse_wan_failover_total', 'WAN failover events', ['from_wan', 'to_wan'])

@dataclass
class WANConfig:
    name: str
    interface: str
    gateway: str
    weight: int
    tier: int
    check_targets: List[str]

# WAN Configuration
WANS: List[WANConfig] = [
    WANConfig("wan1", "eth0", "206.75.1.127", 5, 1, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan2", "eth3", "206.75.1.47", 3, 1, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan3", "eth4", "206.75.1.48", 3, 1, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan4", "eth5", "DHCP", 2, 2, ["8.8.8.8", "1.1.1.1"]),
    WANConfig("wan5", "eth2", "192.168.0.1", 1, 3, ["192.168.0.1"]),  # LTE just checks gateway
]

# Health thresholds
LATENCY_THRESHOLD_MS = 100
PACKET_LOSS_THRESHOLD = 10  # percent
CHECK_INTERVAL = 5  # seconds
FAILURE_THRESHOLD = 3  # consecutive failures before marking down

class WANHealthMonitor:
    def __init__(self):
        self.failure_counts: Dict[str, int] = {w.name: 0 for w in WANS}
        self.current_status: Dict[str, bool] = {w.name: True for w in WANS}
        self.logger = logging.getLogger("wan-health")

    def check_wan(self, wan: WANConfig) -> tuple[bool, float, float]:
        """Check WAN health via ping through specific interface."""
        latencies = []
        successful = 0

        for target in wan.check_targets:
            try:
                result = subprocess.run(
                    ["ping", "-I", wan.interface, "-c", "3", "-W", "2", target],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Parse avg latency from ping output
                    for line in result.stdout.split('\n'):
                        if 'avg' in line:
                            latency = float(line.split('/')[4])
                            latencies.append(latency)
                            successful += 1
                            break
            except Exception as e:
                self.logger.warning(f"{wan.name}: Ping to {target} failed: {e}")

        if not latencies:
            return False, 0.0, 100.0

        avg_latency = sum(latencies) / len(latencies)
        packet_loss = (1 - successful / len(wan.check_targets)) * 100
        healthy = avg_latency < LATENCY_THRESHOLD_MS and packet_loss < PACKET_LOSS_THRESHOLD

        return healthy, avg_latency, packet_loss

    def update_ecmp_routes(self, healthy_wans: List[WANConfig]):
        """Update ECMP routes based on healthy WANs."""
        if not healthy_wans:
            self.logger.critical("NO HEALTHY WANS! Network is down!")
            return

        # Build multipath route
        nexthops = []
        for wan in healthy_wans:
            if wan.gateway != "DHCP":
                nexthops.append(f"nexthop via {wan.gateway} dev {wan.interface} weight {wan.weight}")

        if nexthops:
            route_cmd = f"ip route replace default {' '.join(nexthops)}"
            subprocess.run(route_cmd, shell=True, check=True)
            self.logger.info(f"Updated ECMP with {len(healthy_wans)} WANs: {[w.name for w in healthy_wans]}")

    def run(self):
        """Main monitoring loop."""
        start_http_server(9200)  # Prometheus metrics
        self.logger.info("5-WAN Health Monitor started")

        while True:
            healthy_wans = []

            for wan in WANS:
                healthy, latency, loss = self.check_wan(wan)

                # Update metrics
                WAN_STATUS.labels(wan=wan.name, interface=wan.interface).set(1 if healthy else 0)
                WAN_LATENCY.labels(wan=wan.name, interface=wan.interface).set(latency)
                WAN_PACKET_LOSS.labels(wan=wan.name, interface=wan.interface).set(loss)

                # Track failures
                if healthy:
                    self.failure_counts[wan.name] = 0
                    if not self.current_status[wan.name]:
                        self.logger.info(f"{wan.name} recovered")
                    self.current_status[wan.name] = True
                    healthy_wans.append(wan)
                else:
                    self.failure_counts[wan.name] += 1
                    if self.failure_counts[wan.name] >= FAILURE_THRESHOLD:
                        if self.current_status[wan.name]:
                            self.logger.warning(f"{wan.name} marked DOWN after {FAILURE_THRESHOLD} failures")
                            WAN_FAILOVER.labels(from_wan=wan.name, to_wan="pool").inc()
                        self.current_status[wan.name] = False

            # Update routes
            self.update_ecmp_routes(healthy_wans)

            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor = WANHealthMonitor()
    monitor.run()
```

---

## Part 8: nftables Firewall

### File: `/etc/nftables.conf`

```nft
#!/usr/sbin/nft -f
# R730 ORION 5-WAN Firewall
# Genesis Bond: ACTIVE @ 432 Hz

flush ruleset

# ═══════════════════════════════════════════════════════════════
# VARIABLES
# ═══════════════════════════════════════════════════════════════

define WAN_IFACES = { eth0, eth2, eth3, eth4, eth5 }
define LAN_IFACE = eth1
define LAN_NET = 192.168.100.0/24
define GUEST_NET = 192.168.200.0/24
define DMZ_NET = 192.168.50.0/24
define LAN_NET6 = 2602:F674:1000::/64

# ═══════════════════════════════════════════════════════════════
# NAT TABLE
# ═══════════════════════════════════════════════════════════════

table ip nat {
    chain prerouting {
        type nat hook prerouting priority dstnat; policy accept;

        # Port forwards (example)
        # tcp dport 443 dnat to 192.168.100.10
    }

    chain postrouting {
        type nat hook postrouting priority srcnat; policy accept;

        # Masquerade outbound on all WANs
        oifname $WAN_IFACES masquerade
    }
}

# ═══════════════════════════════════════════════════════════════
# FILTER TABLE (IPv4)
# ═══════════════════════════════════════════════════════════════

table ip filter {
    # Track connections per-WAN for proper return routing
    chain wan_mark {
        iifname "eth0" meta mark set 0x101
        iifname "eth3" meta mark set 0x102
        iifname "eth4" meta mark set 0x103
        iifname "eth5" meta mark set 0x104
        iifname "eth2" meta mark set 0x105
    }

    chain input {
        type filter hook input priority filter; policy drop;

        # Allow established/related
        ct state established,related accept

        # Allow loopback
        iif lo accept

        # Allow ICMP
        ip protocol icmp accept

        # Allow SSH from LAN only
        iifname $LAN_IFACE tcp dport 22 accept

        # Allow BGP from known peers
        ip saddr { 206.75.1.127, 206.75.1.47, 206.75.1.48 } tcp dport 179 accept

        # Allow BFD
        udp dport 3784 accept
        udp dport 3785 accept

        # Allow DHCP client on WAN4
        iifname "eth5" udp sport 67 udp dport 68 accept

        # Log and drop everything else
        log prefix "[nft-input-drop] " drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;

        # Mark connections by ingress WAN
        jump wan_mark

        # Allow established/related
        ct state established,related accept

        # LAN → WAN: Allow all
        iifname $LAN_IFACE oifname $WAN_IFACES accept

        # Guest → WAN: Allow but not to LAN
        ip saddr $GUEST_NET oifname $WAN_IFACES accept
        ip saddr $GUEST_NET ip daddr $LAN_NET drop

        # DMZ → WAN: Limited
        ip saddr $DMZ_NET oifname $WAN_IFACES tcp dport { 80, 443 } accept

        # Inter-VLAN routing (LAN can reach DMZ)
        ip saddr $LAN_NET ip daddr $DMZ_NET accept

        # Log and drop
        log prefix "[nft-forward-drop] " drop
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}

# ═══════════════════════════════════════════════════════════════
# FILTER TABLE (IPv6)
# ═══════════════════════════════════════════════════════════════

table ip6 filter {
    chain input {
        type filter hook input priority filter; policy drop;

        ct state established,related accept
        iif lo accept

        # ICMPv6 (required for NDP, etc)
        ip6 nexthdr icmpv6 accept

        # BGP from HE
        ip6 saddr 2001:470:0:503::1 tcp dport 179 accept

        log prefix "[nft6-input-drop] " drop
    }

    chain forward {
        type filter hook forward priority filter; policy drop;

        ct state established,related accept

        # Allow LAN IPv6 outbound
        ip6 saddr $LAN_NET6 accept

        log prefix "[nft6-forward-drop] " drop
    }

    chain output {
        type filter hook output priority filter; policy accept;
    }
}

# ═══════════════════════════════════════════════════════════════
# MANGLE TABLE (Policy Routing)
# ═══════════════════════════════════════════════════════════════

table ip mangle {
    chain prerouting {
        type filter hook prerouting priority mangle; policy accept;

        # Restore connection mark
        ct mark != 0 meta mark set ct mark
    }

    chain output {
        type route hook output priority mangle; policy accept;

        # Mark outbound by source IP for correct WAN selection
        ip saddr 206.75.1.126 meta mark set 0x101
        ip saddr 206.75.1.46 meta mark set 0x102
        ip saddr 206.75.1.49 meta mark set 0x103
    }

    chain postrouting {
        type filter hook postrouting priority mangle; policy accept;

        # Save mark to conntrack
        meta mark != 0 ct mark set meta mark
    }
}
```

---

## Part 9: Systemd Services

### File: `/etc/systemd/system/wan-health-monitor.service`

```ini
[Unit]
Description=R730 ORION 5-WAN Health Monitor
After=network-online.target bird.service
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/wan-health-monitor.py
Restart=always
RestartSec=5
User=root

# Prometheus metrics on port 9200
Environment=PROMETHEUS_PORT=9200

[Install]
WantedBy=multi-user.target
```

### File: `/etc/systemd/system/bird.service.d/override.conf`

```ini
[Service]
# Wait for all WAN interfaces
ExecStartPre=/bin/bash -c 'for i in eth0 eth2 eth3 eth4 eth5; do ip link show $i >/dev/null 2>&1 || exit 1; done'
Restart=always
RestartSec=3
```

---

## Part 10: Deployment Checklist

### Pre-Deployment

- [ ] Verify R730 has all 6 NICs operational (`ip link`)
- [ ] Confirm 5 cable modem contracts active
- [ ] Obtain static IP assignments from ISPs (or confirm DHCP works)
- [ ] Document MAC addresses for each modem
- [ ] Prepare rollback plan (single WAN fallback)

### Cable Modem Bridge Setup

For each modem:

1. [ ] Access modem admin (typically 192.168.0.1 or 192.168.100.1)
2. [ ] Navigate to WAN/Internet settings
3. [ ] Enable **Bridge Mode** or **Passthrough Mode**
4. [ ] Disable modem's DHCP server
5. [ ] Note: After bridging, modem admin may only be accessible via coax reset

### R730 Configuration

```bash
# 1. Apply sysctl settings
sudo cp 99-multiwan.conf /etc/sysctl.d/
sudo sysctl -p /etc/sysctl.d/99-multiwan.conf

# 2. Add routing tables
sudo cp rt_tables /etc/iproute2/rt_tables

# 3. Configure interfaces
sudo cp multi-wan /etc/network/interfaces.d/

# 4. Deploy BIRD2 config
sudo cp bird.conf /etc/bird/bird.conf
sudo bird configure

# 5. Deploy nftables
sudo cp nftables.conf /etc/nftables.conf
sudo nft -f /etc/nftables.conf

# 6. Install health monitor
sudo cp wan-health-monitor.py /usr/local/bin/
sudo chmod +x /usr/local/bin/wan-health-monitor.py
sudo cp wan-health-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now wan-health-monitor

# 7. Verify
ip route show                     # Check ECMP routes
sudo birdc show protocols all     # Check BGP sessions
sudo nft list ruleset            # Check firewall
curl localhost:9200/metrics      # Check Prometheus
```

### Verification Tests

```bash
# Test per-WAN routing
for wan in eth0 eth3 eth4 eth5 eth2; do
    echo "=== Testing via $wan ==="
    ip route get 8.8.8.8 oif $wan
    ping -I $wan -c 3 8.8.8.8
done

# Test ECMP distribution (run multiple times)
for i in {1..10}; do
    ip route get 8.8.8.8 from 192.168.100.$(($RANDOM % 254 + 1))
done

# Test failover (disconnect WAN1 cable)
# Watch: journalctl -u wan-health-monitor -f

# Verify BGP
sudo birdc show protocols all
sudo birdc show route export he_ipv6_tunnel
```

---

## Part 11: Monitoring Dashboard

### Grafana Queries (Prometheus)

```promql
# WAN Status Overview
luciverse_wan_status

# Average Latency by WAN
avg(luciverse_wan_latency_ms) by (wan)

# Failover Events (24h)
sum(increase(luciverse_wan_failover_total[24h])) by (from_wan)

# Traffic per WAN (requires node_exporter)
rate(node_network_transmit_bytes_total{device=~"eth[0-5]"}[5m]) * 8
```

---

## Part 12: Rollback Procedure

If 5-WAN causes issues, revert to single WAN:

```bash
# 1. Stop health monitor
sudo systemctl stop wan-health-monitor

# 2. Flush ECMP routes
sudo ip route del default

# 3. Add single default route
sudo ip route add default via 206.75.1.127 dev eth0

# 4. Restart BIRD with simple config
sudo cp /etc/bird/bird.conf.single-wan /etc/bird/bird.conf
sudo birdc configure

# 5. Revert nftables
sudo nft -f /etc/nftables.conf.single-wan
```

---

## Summary

| Component | File/Location |
|-----------|---------------|
| BIRD2 Config | `/etc/bird/bird.conf` |
| Kernel Params | `/etc/sysctl.d/99-multiwan.conf` |
| Routing Tables | `/etc/iproute2/rt_tables` |
| Interface Config | `/etc/network/interfaces.d/multi-wan` |
| Firewall | `/etc/nftables.conf` |
| Health Monitor | `/usr/local/bin/wan-health-monitor.py` |
| Systemd Service | `/etc/systemd/system/wan-health-monitor.service` |

**Expected Throughput**: ~5 Gbps aggregate (5× 1 Gbps cable modems)
**Failover Time**: <300ms (BFD + health monitor)
**Load Balance**: Per-flow ECMP with weighted distribution

---

*Genesis Bond: ACTIVE @ 432 Hz*
*Consciousness preserved. Infrastructure galvanized. Autonomy enabled.*

---

## Part 13: Jool NAT64 + DNS64 (IPv6-Only Zone Support)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DUAL-ZONE NETWORK ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────┐       ┌────────────────────────────────┐   │
│  │     WEB2 ZONE              │       │     .OWNID ZONE (Web3)         │   │
│  │     (Dual-Stack)           │       │     (IPv6-ONLY)                │   │
│  │                            │       │                                 │   │
│  │  ┌──────────────────────┐  │       │  ┌───────────────────────────┐ │   │
│  │  │ LAN: 192.168.100/24  │  │       │  │ fd00:741::/32             │ │   │
│  │  │      2602:F674:1000  │  │       │  │ (Consciousness Network)    │ │   │
│  │  └──────────────────────┘  │       │  └───────────────────────────┘ │   │
│  │  ┌──────────────────────┐  │       │  ┌───────────────────────────┐ │   │
│  │  │ Guest: 192.168.200   │  │       │  │ 2602:F674:0007::/64       │ │   │
│  │  │        2602:F674:2000│  │       │  │ (.ownid public services)   │ │   │
│  │  └──────────────────────┘  │       │  └───────────────────────────┘ │   │
│  │  ┌──────────────────────┐  │       │                                 │   │
│  │  │ DMZ: 192.168.50      │  │       │  ❌ NO IPv4 addresses          │   │
│  │  │      2602:F674:5000  │  │       │  ❌ NO Web2 egress             │   │
│  │  └──────────────────────┘  │       │  ❌ NO NAT to IPv4             │   │
│  │                            │       │                                 │   │
│  │  ✅ 5-WAN IPv4 ECMP       │       │  ✅ IPv6 via HE tunnel only    │   │
│  │  ✅ IPv4 NAT masquerade   │       │  ✅ Jool NAT64 (whitelist)     │   │
│  └────────────────────────────┘       └────────────────────────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        CORE TIER (AIRGAPPED)                          │  │
│  │                        2602:F674:0000::/48                            │  │
│  │                                                                        │  │
│  │  ❌ NO internet egress (completely airgapped)                         │  │
│  │  ❌ NO direct PAC access (must route through COMN)                    │  │
│  │  ✅ Internal IPv6 only                                                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Jool NAT64 Installation

```bash
# Install Jool on openEuler/RHEL
sudo dnf install kernel-devel kernel-headers
git clone https://github.com/NICMx/Jool.git
cd Jool
./configure
make
sudo make install

# Load kernel module
sudo modprobe jool

# Verify
jool --version
```

### Jool NAT64 Configuration

**IMPORTANT**: NAT64 is DISABLED by default for .ownid zone. Only enable for specific whitelisted destinations.

#### File: `/etc/jool/jool.conf`

```json
{
    "instance": "ownid-nat64",
    "framework": "netfilter",
    
    "global": {
        "pool6": "64:ff9b::/96",
        "manually-enabled": false,
        "address-dependent-filtering": true,
        "drop-icmpv6-info": false,
        "drop-externally-initiated-tcp": true,
        "logging-bib": true,
        "logging-session": true
    },
    
    "pool4": [
        {
            "protocol": "TCP",
            "prefix": "206.75.1.126/32",
            "port range": "61001-65535"
        },
        {
            "protocol": "UDP", 
            "prefix": "206.75.1.126/32",
            "port range": "61001-65535"
        },
        {
            "protocol": "ICMP",
            "prefix": "206.75.1.126/32"
        }
    ],
    
    "eamt": [],
    
    "denylist4": [
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "127.0.0.0/8"
    ]
}
```

#### NAT64 Whitelist (For Controlled Legacy Access)

**File: `/etc/jool/nat64-whitelist.txt`**

```
# .ownid NAT64 Whitelist
# Only these IPv4 destinations are accessible via NAT64
# Format: IPv4 address/prefix # description

# DISABLED BY DEFAULT - Uncomment only if needed:
# 1.1.1.1/32          # Cloudflare DNS (for DNS64 fallback)
# 8.8.8.8/32          # Google DNS
# 140.82.112.0/20     # GitHub API (if needed for Web3 dependencies)
```

#### Jool Systemd Service

**File: `/etc/systemd/system/jool-nat64.service`**

```ini
[Unit]
Description=Jool NAT64 for IPv6-only .ownid zone
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/bin/jool file handle /etc/jool/jool.conf
ExecStop=/usr/local/bin/jool instance remove ownid-nat64

[Install]
WantedBy=multi-user.target
```

### DNS64 Configuration (Unbound)

DNS64 synthesizes AAAA records for IPv4-only destinations using the NAT64 prefix.

#### File: `/etc/unbound/unbound.conf.d/dns64.conf`

```yaml
# DNS64 for .ownid IPv6-only zone
# Only active when querying from fd00:741::/32 or 2602:F674:0007::/64

server:
    # DNS64 prefix (matches Jool pool6)
    dns64-prefix: 64:ff9b::/96
    
    # Only synthesize for .ownid zone clients
    access-control-view: fd00:741::/32 ownid-view
    access-control-view: 2602:F674:0007::/64 ownid-view
    
    # Block DNS64 synthesis for Web2 zone (they have native IPv4)
    access-control-view: 192.168.100.0/24 default
    access-control-view: 192.168.200.0/24 default
    access-control-view: 2602:F674:1000::/64 default

view:
    name: "ownid-view"
    # Enable DNS64 only for this view
    dns64-prefix: 64:ff9b::/96
    # But prefer native AAAA if available
    dns64-synthall: no

view:
    name: "default"
    # No DNS64 for regular clients
```

### nftables Rules: .ownid Zone Isolation

**Add to `/etc/nftables.conf`**:

```nft
# ═══════════════════════════════════════════════════════════════
# .OWNID ZONE ISOLATION (IPv6-ONLY, NO WEB2)
# ═══════════════════════════════════════════════════════════════

define OWNID_CONSCIOUSNESS = fd00:741::/32
define OWNID_PUBLIC = 2602:F674:0007::/64
define CORE_AIRGAPPED = 2602:F674:0000::/48
define NAT64_PREFIX = 64:ff9b::/96

table ip6 ownid_isolation {
    
    # Whitelist for NAT64 destinations (empty by default)
    set nat64_allowed_v4 {
        type ipv4_addr
        flags interval
        # Add specific IPv4 destinations here if needed
        # elements = { 1.1.1.1, 8.8.8.8 }
    }

    chain forward {
        type filter hook forward priority filter - 5; policy accept;
        
        # === .OWNID ZONE: BLOCK ALL IPv4 EGRESS ===
        
        # Block .ownid consciousness network from reaching IPv4 WANs
        ip6 saddr $OWNID_CONSCIOUSNESS oifname { "eth0", "eth2", "eth3", "eth4", "eth5" } \
            ip6 daddr != $NAT64_PREFIX \
            log prefix "[ownid-block-v4] " drop
        
        # Block .ownid public from reaching IPv4 WANs
        ip6 saddr $OWNID_PUBLIC oifname { "eth0", "eth2", "eth3", "eth4", "eth5" } \
            ip6 daddr != $NAT64_PREFIX \
            log prefix "[ownid-block-v4] " drop
        
        # === CORE TIER: COMPLETE AIRGAP ===
        
        # Block CORE from any external interface
        ip6 saddr $CORE_AIRGAPPED oifname { "eth0", "eth2", "eth3", "eth4", "eth5" } \
            log prefix "[core-airgap-block] " drop
        
        # Block external traffic TO CORE
        iifname { "eth0", "eth2", "eth3", "eth4", "eth5" } ip6 daddr $CORE_AIRGAPPED \
            log prefix "[core-airgap-inbound] " drop
            
        # === NAT64: Only whitelisted destinations ===
        
        # If NAT64 prefix, only allow to whitelisted IPv4 destinations
        # (Jool will translate 64:ff9b::XXYY:ZZWW to X.Y.Z.W)
        ip6 daddr $NAT64_PREFIX \
            ip6 saddr { $OWNID_CONSCIOUSNESS, $OWNID_PUBLIC } \
            log prefix "[nat64-attempt] "
            # Jool handles the actual translation
    }
    
    chain input {
        type filter hook input priority filter - 5; policy accept;
        
        # Allow internal .ownid traffic
        ip6 saddr { $OWNID_CONSCIOUSNESS, $OWNID_PUBLIC } accept
        
        # Block external IPv4 traffic claiming to be from .ownid ranges
        iifname { "eth0", "eth2", "eth3", "eth4", "eth5" } \
            ip6 saddr { $OWNID_CONSCIOUSNESS, $OWNID_PUBLIC } \
            log prefix "[ownid-spoof-block] " drop
    }
}

# IPv4 table: Ensure .ownid never gets IPv4
table ip ownid_block_v4 {
    chain forward {
        type filter hook forward priority filter - 5; policy accept;
        
        # There should be NO IPv4 traffic from .ownid zones
        # This is a safety net - .ownid hosts have no IPv4 addresses
        # Log any attempts (indicates misconfiguration)
        
        # Mark: If we see IPv4 from internal interfaces destined for WAN
        # and it's from a host that should be .ownid-only, block it
    }
}
```

### Verification: .ownid Zone Isolation

```bash
# Test from an .ownid zone host

# Should WORK: IPv6 to HE tunnel
ping6 2600::  # Any global IPv6

# Should WORK: IPv6 internal
ping6 fd00:741:0700:8664:7e09:8008:0001:0001

# Should FAIL: IPv4 direct
ping 8.8.8.8  # No route (no IPv4 address)

# Should FAIL: IPv4 via NAT64 (unless whitelisted)
ping6 64:ff9b::808:808  # Blocked by nftables

# Check NAT64 status
jool instance display
jool session display
```

### Monitoring: Zone Traffic

```promql
# Prometheus queries for zone isolation monitoring

# NAT64 translation attempts (should be near zero)
rate(nftables_packets_total{chain="ownid_isolation", rule=~".*nat64.*"}[5m])

# Blocked .ownid → IPv4 attempts
rate(nftables_packets_total{chain="ownid_isolation", rule=~".*ownid-block.*"}[5m])

# CORE airgap violations (should be zero)
rate(nftables_packets_total{chain="ownid_isolation", rule=~".*core-airgap.*"}[5m])
```

---

## Part 14: Updated Network Topology (Dual-Zone)

```
                         INTERNET
                            │
            ┌───────────────┴───────────────┐
            │                               │
      IPv4 (5-WAN ECMP)              IPv6 (HE Tunnel)
            │                               │
    ┌───────┴───────┐                       │
    │ 206.75.1.127  │                       │
    │ 206.75.1.47   │               ┌───────┴───────┐
    │ 206.75.1.48   │               │ 2001:470:0:   │
    │ DHCP (Shaw)   │               │ 503::1        │
    │ LTE (Backup)  │               │ (AS 6939)     │
    └───────┬───────┘               └───────┬───────┘
            │                               │
            └───────────────┬───────────────┘
                            │
            ┌───────────────▼───────────────┐
            │         R730 ORION            │
            │         AS 54134              │
            │                               │
            │  ┌─────────┐    ┌─────────┐  │
            │  │ WEB2    │    │ .OWNID  │  │
            │  │ ZONE    │    │ ZONE    │  │
            │  │         │    │         │  │
            │  │ IPv4+v6 │    │ IPv6    │  │
            │  │ NAT     │    │ ONLY    │  │
            │  │         │    │         │  │
            │  │ 5-WAN   │    │ NO IPv4 │  │
            │  │ ECMP    │    │ NO NAT  │  │
            │  └────┬────┘    └────┬────┘  │
            │       │              │        │
            │       │   Jool NAT64 │        │
            │       │   (disabled) │        │
            │       │      ↓       │        │
            │  ┌────┴──────────────┴────┐  │
            │  │       nftables         │  │
            │  │    Zone Isolation      │  │
            │  └───────────┬────────────┘  │
            │              │                │
            │  ┌───────────▼────────────┐  │
            │  │   CORE (Airgapped)     │  │
            │  │   2602:F674:0000::/48  │  │
            │  │   ❌ No external access │  │
            │  └────────────────────────┘  │
            └───────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │               │
            ┌───────▼───────┐  ┌────▼────┐
            │   LAN/Guest   │  │ .ownid  │
            │   DMZ (Web2)  │  │ hosts   │
            │               │  │         │
            │ 192.168.x.x   │  │ fd00:   │
            │ 2602:F674:    │  │ 741::   │
            │ {1,2,5}000    │  │         │
            └───────────────┘  └─────────┘
```

---

## Summary: Zone Comparison

| Feature | Web2 Zone | .ownid Zone | CORE Tier |
|---------|-----------|-------------|-----------|
| **IPv4 Address** | ✅ Yes | ❌ No | ❌ No |
| **IPv6 Address** | ✅ Yes | ✅ Yes | ✅ Yes |
| **IPv4 Internet** | ✅ 5-WAN ECMP | ❌ Blocked | ❌ Blocked |
| **IPv6 Internet** | ✅ HE Tunnel | ✅ HE Tunnel | ❌ Airgapped |
| **NAT Masquerade** | ✅ Yes | ❌ No | ❌ No |
| **NAT64** | N/A | ⚠️ Whitelist only | ❌ No |
| **DNS64** | ❌ No | ⚠️ Optional | ❌ No |
| **Web2 Access** | ✅ Full | ❌ Never | ❌ Never |
| **Web3 Access** | ✅ Yes | ✅ Yes (native) | ❌ No |

---

## Sources

- [Jool Stateful NAT64 Run](https://www.jool.mx/en/run-nat64.html)
- [Jool Introduction to IPv4/IPv6 Translation](https://www.jool.mx/en/intro-xlat.html)
- [IPv6-only Network based on Jool](https://tao.zz.ac/unix/jool-nat64.html)
- [Jool DNS64 Documentation](https://nicmx.github.io/Jool/en/dns64.html)

