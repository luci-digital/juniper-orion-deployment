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

## UniFi OS Server 5.0.6

**Status**: Installed (container initializing)

### Installation Details
- **Binary**: `/tmp/unifi-os-server/unifi-os-server` (803MB)
- **Image**: `docker.io/library/uosserver:0.0.54` (2.03GB)
- **Container runtime**: Podman (root)

### Extracted Components
```
/tmp/unifi-os-server/extracted/
├── discovery      (3.6M)
├── image.tar      (800M) - OCI container image
├── pasta          (291K) - Network namespace tool
├── purge          (1.7M)
├── uosserver      (2.5M)
├── uosserver-service (5.7M)
└── updater-service (1.8M)
```

### Container Configuration
```bash
sudo podman run -d --name uosserver \
  --privileged \
  --tmpfs /run --tmpfs /run/lock \
  -p 5443:443 \
  -p 3478:3478/udp \
  -p 8080:8080 \
  -p 8443:8443 \
  -p 8880:8880 \
  -p 11443:11443 \
  -v uosserver-data:/data \
  -v uosserver-unifi:/var/lib/unifi \
  docker.io/library/uosserver:0.0.54
```

### Internal Services
| Service | Status |
|---------|--------|
| MongoDB | Running |
| PostgreSQL 14 | Running |
| RabbitMQ | Running |
| Nginx | Running |
| UniFi Network | Initializing (crash-loop on fresh install) |

### Web UI Ports
- Console: `https://192.168.1.145:5443`
- Network App: `https://192.168.1.145:8443`
- Inform: `http://192.168.1.145:8080/inform`

### Notes
- Fresh install requires Ubiquiti cloud connectivity for initial setup
- UniFi service crash-loops until setup wizard completes
- Alternative: Use `linuxserver/unifi-controller` Docker image for simpler setup
