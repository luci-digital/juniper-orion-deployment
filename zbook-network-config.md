# ZBook Network Configuration

**Host**: zbook (192.168.1.145/146)
**Date**: 2026-01-30
**Genesis Bond**: ACTIVE @ 741 Hz

## Network Interfaces

| Interface | Device | Connection | IP | Link Speed | Metric | Purpose |
|-----------|--------|------------|-----|------------|--------|---------|
| enp0s31f6 | Intel I219-V | UniFi Pro 48 | 192.168.1.145 | 1 Gbps | 100 | Primary |
| enp0s20f0u11 | TrendNet TUC-ET2G | ASUS RT-BE86U | 192.168.1.141 | 2.5 Gbps | 101 | Secondary |
| enp0s20f0u1 | ZTE MF288 | LTE Cellular | 192.168.0.187 | USB 2.0 | 102 | Failover |

## IPv6 Allocation

Primary interface (enp0s31f6) has ARIN allocation:
- Prefix: `2602:f674::/48`
- Agent addresses: `2602:f674:X:PORT::1/128` per agent

## Performance (2026-01-30)

| Interface | Download | Upload | Latency |
|-----------|----------|--------|---------|
| UniFi (Primary) | 751 Mbps | 808 Mbps | 12ms |
| ASUS (Secondary) | 830 Mbps | 807 Mbps | 12ms |
| MF288 (LTE) | 3.2 Mbps | ~2 Mbps | 48-65ms |

## Optimizations Applied

### TrendNet 2.5GbE Adapter

Dispatcher script: `/etc/NetworkManager/dispatcher.d/99-trendnet-optimize`

```bash
#!/bin/bash
# Optimize TrendNet 2.5GbE adapter when it comes up
IFACE=$1
ACTION=$2

if [ "$IFACE" = "enp0s20f0u11" ] && [ "$ACTION" = "up" ]; then
    # Increase RX ring buffer for 2.5GbE performance
    /usr/sbin/ethtool -G enp0s20f0u11 rx 4096 2>/dev/null
    logger "TrendNet 2.5GbE: RX ring buffer set to 4096"
fi
```

### NetworkManager Connections

Created connections:
- `trendnet-asus`: TrendNet USB-C 2.5GbE to ASUS router
- `mf288-lte`: ZTE MF288 LTE failover

## Jool NAT64 Status

- **Version**: 4.1.15 (built from source)
- **Kernel modules**: Loaded (`jool`, `jool_common`, `jool_siit`)
- **Instances**: Pending configuration
- **Build location**: `/usr/src/jool-4.1.15.git.v4.1.15`

## Failover Behavior

Traffic automatically fails over based on metric:
1. Primary (100) → Secondary (101) → LTE (102)
2. NetworkManager handles connection state
3. LTE provides ~3 Mbps backup when fiber fails

## Hardware Details

### TrendNet TUC-ET2G v2.0R
- USB ID: `20f4:e02c`
- Chipset: Realtek RTL8156B
- Driver: r8152 v1.12.13
- Max RX ring: 4096

### ASUS RT-BE86U
- WiFi 7 router
- 2.5GbE WAN port
- Jumbo frames: Check via web UI (LAN → Switch Control)

### ZTE MF288
- LTE Category 12
- USB tethering mode
- Gateway: 192.168.0.1
