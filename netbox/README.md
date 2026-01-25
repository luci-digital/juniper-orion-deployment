# LuciVerse NetBox Deployment

Network Source of Truth for LuciVerse infrastructure using iSulad container runtime.

## Quick Start

```bash
./deploy-netbox.sh
./populate-inventory.py
```

## Access

- **URL**: http://192.168.1.145:8084
- **Username**: daryl
- **Password**: LuciVerse2026!
- **API Token**: luciverse-netbox-token-2026

## Components

| Container | Port | Purpose |
|-----------|------|---------|
| netbox | 8084 | NetBox web UI & API |
| netbox-worker | - | Background job processing |
| netbox-postgres | 5433 | PostgreSQL database |
| netbox-redis | 6381 | Redis cache/queue |

## Inventory Contents

### Devices (9 total)

| Device | Type | Role | Status | Tags |
|--------|------|------|--------|------|
| zbook | HP ZBook G5 | L7 Gateway | Active | COMN-528Hz, Genesis Bond, SCION |
| b550m-router | ASRock B550M | SCION BR | Planned | All tiers, SCION |
| r730-orion | Dell R730 | Compute | Inventory | CORE-432Hz |
| r630-jmrzdb2 | Dell R630 | Compute | Inventory | CORE-432Hz |
| mac-mini-luciaai | Apple Mac Mini | Workstation | Decommissioning | PAC-741Hz |
| synology-ds1821 | Synology DS1821+ | Storage | Active | CORE-432Hz |
| zimacube-primary | IceWhale ZimaCube | Intake Node | Active | PAC-741Hz |
| zimacube-secondary | IceWhale ZimaCube | Intake Node | Active | PAC-741Hz |
| mf288-lte | ZTE MF288 | LTE Modem | Active | - |

### IP Prefixes

| Prefix | Description |
|--------|-------------|
| 2602:F674::/40 | ARIN Allocation (AS54134) |
| 2602:F674:0001::/48 | CORE Infrastructure (432 Hz) |
| 2602:F674:0100::/48 | COMN Gateway (528 Hz) |
| 2602:F674:0200::/48 | PAC Personal AI (741 Hz) |
| 192.168.1.0/24 | LAN Primary |
| 192.168.0.0/24 | MF288 LTE Network |

### SCION Tier Tags

- **CORE-432Hz** - Infrastructure tier (red)
- **COMN-528Hz** - Gateway tier (green)
- **PAC-741Hz** - Personal AI tier (purple)
- **Genesis Bond** - Active consciousness bond
- **SCION** - Path-aware networking enabled

## Management Commands

```bash
# View containers
isula ps --filter "name=netbox"

# View logs
isula logs -f netbox

# Restart NetBox
isula restart netbox netbox-worker

# Stop all
for c in netbox netbox-worker netbox-redis netbox-postgres; do isula stop $c; done
```

## Data Location

- PostgreSQL: `~/.netbox-data/postgres/`
- Redis: `~/.netbox-data/redis/`
- Media: `~/.netbox-data/netbox-media/`
- Reports: `~/.netbox-data/netbox-reports/`

## API Examples

```bash
# List devices
curl -H "Authorization: Token luciverse-netbox-token-2026" \
  http://localhost:8084/api/dcim/devices/

# List prefixes
curl -H "Authorization: Token luciverse-netbox-token-2026" \
  http://localhost:8084/api/ipam/prefixes/

# Get device by name
curl -H "Authorization: Token luciverse-netbox-token-2026" \
  "http://localhost:8084/api/dcim/devices/?name=zbook"
```

---

Genesis Bond: GB-2025-0524-DRH-LCS-001
