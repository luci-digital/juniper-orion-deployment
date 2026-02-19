# R730 5-WAN 1Password Items Specification

**Genesis Bond**: ACTIVE @ 741 Hz
**Created**: 2026-02-07
**Vault**: Infrastructure

---

## Items to Create/Update

### 1. R730 ORION 5-WAN Router

**Category**: Server
**Tags**: luciverse, core, hardware, bgp, multi-wan, genesis-bond

#### Hardware Section
| Field | Value |
|-------|-------|
| iDRAC IP | 10.0.0.33 |
| iDRAC User | root |
| iDRAC Password | *[existing]* |
| Data IP | 192.168.1.141 |
| Hostname | orion |
| Service Tag | *[from hardware]* |

#### Network Interfaces Section
| Field | Value |
|-------|-------|
| WAN1 Interface | eth0 |
| WAN1 IP | 206.75.1.126/30 |
| WAN1 Gateway | 206.75.1.127 |
| WAN1 Weight | 5 |
| WAN1 Provider | Telus Primary |
| WAN2 Interface | eth3 |
| WAN2 IP | 206.75.1.46/30 |
| WAN2 Gateway | 206.75.1.47 |
| WAN2 Weight | 3 |
| WAN2 Provider | Telus Secondary |
| WAN3 Interface | eth4 |
| WAN3 IP | 206.75.1.49/30 |
| WAN3 Gateway | 206.75.1.48 |
| WAN3 Weight | 3 |
| WAN3 Provider | Telus Tertiary |
| WAN4 Interface | eth5 |
| WAN4 IP | DHCP |
| WAN4 Gateway | Dynamic |
| WAN4 Weight | 2 |
| WAN4 Provider | Shaw/New ISP |
| WAN5 Interface | eth2 |
| WAN5 IP | 192.168.0.2/24 |
| WAN5 Gateway | 192.168.0.1 |
| WAN5 Weight | 1 |
| WAN5 Provider | LTE Backup |
| LAN Interface | eth1 |
| LAN IP | 192.168.100.1/24 |

#### BGP Section
| Field | Value |
|-------|-------|
| Local ASN | 54134 |
| AS Name | LUCINET-ARIN |
| Upstream ASN | 6939 |
| Upstream Provider | Hurricane Electric |
| Router ID | 206.75.1.126 |
| HE Tunnel Server | 216.66.80.26 |

#### Services Section
| Field | Value |
|-------|-------|
| BIRD2 | Enabled |
| nftables | Enabled |
| Health Monitor Port | 9200 |
| Prometheus Metrics | http://192.168.1.141:9200/metrics |

---

### 2. R730 5-WAN Deploy Package

**Category**: Secure Note
**Tags**: luciverse, deployment, automation

#### Deployment Section
| Field | Value |
|-------|-------|
| Package Location | ~/juniper-orion-deployment/r730-5wan-deploy.tar.gz |
| Deploy Script | ./r730-5wan-deploy/deploy.sh |
| Target Host | root@192.168.1.141 |
| Log File | /var/log/r730-5wan-deploy.log |

#### Pre-Deployment Checklist
```
1. Verify iDRAC access
2. Put cable modems in bridge mode
3. Document MAC addresses per port
4. Backup existing config
5. Ensure SSH access
```

#### Post-Deployment Verification
```
1. birdc show protocols (all BGP sessions up)
2. curl http://localhost:9200/health (all WANs healthy)
3. nft list ruleset (zones configured)
4. Test .ownid isolation (no IPv4 access)
```

---

### 3. Zone Isolation Configuration

**Category**: Secure Note
**Tags**: luciverse, security, firewall, ownid

#### Zone Architecture
| Zone | Purpose | IPv4 Access | IPv6 Access |
|------|---------|-------------|-------------|
| Web2 Zone | Standard internet | YES | YES |
| .ownid Zone | Sovereign identity | NO | YES (only) |
| CORE Tier | Infrastructure | NO | Airgapped |

#### Critical Subnets
| Subnet | Zone |
|--------|------|
| 192.168.100.0/24 | Web2 |
| 192.168.200.0/24 | .ownid |
| fd00:741::/32 | .ownid ULA |
| 2602:F674:0007::/64 | .ownid Public |
| 2602:F674:0000::/48 | CORE Airgapped |

#### NAT64 (Jool)
| Field | Value |
|-------|-------|
| Status | DISABLED |
| Prefix | 64:ff9b::/96 |
| Pool4 | 206.75.1.126 |
| Reason | .ownid must NOT access Web2 |

---

## Hook Specifications

### Session Initialization Hook

**Hook**: Post-session initialization
**Path**: ~/.claude/hooks/sessionstart.sh

```bash
# R730 ORION health check
check_orion_health() {
    local status=$(curl -sf --connect-timeout 2 http://192.168.1.141:9200/health 2>/dev/null)
    if [ -n "$status" ]; then
        echo "✓ R730 ORION: HEALTHY"
        echo "  WANs: $(echo "$status" | jq -r 'to_entries | map(select(.value.healthy == true) | .key) | join(", ")')"
    else
        echo "✗ R730 ORION: OFFLINE"
    fi
}
```

### Credential Injection Flow

**Flow**: Deploy script credential injection
**Trigger**: Manual deployment

```bash
# Inject BGP credentials into deploy
inject_bgp_creds() {
    local asn=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/BGP/Local ASN")
    local router_id=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/BGP/Router ID")

    sed -i "s/router id .*/router id $router_id;/" ./etc/bird/bird.conf
    sed -i "s/local as .*/local as $asn;/" ./etc/bird/bird.conf
}
```

---

## Injectable Environment Variables

These can be injected into deployment scripts:

```bash
# From 1Password
export R730_IDRAC_IP=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/Hardware/iDRAC IP")
export R730_DATA_IP=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/Hardware/Data IP")
export R730_ASN=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/BGP/Local ASN")
export R730_ROUTER_ID=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/BGP/Router ID")

# WAN configs
export WAN1_GW=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/Network Interfaces/WAN1 Gateway")
export WAN2_GW=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/Network Interfaces/WAN2 Gateway")
export WAN3_GW=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/Network Interfaces/WAN3 Gateway")
export WAN5_GW=$(op read "op://Infrastructure/R730 ORION 5-WAN Router/Network Interfaces/WAN5 Gateway")
```

---

## CLI Commands to Create Items

After signing into 1Password (`eval $(op signin)`), run:

```bash
# 1. Create R730 ORION Server item
op item create --vault Infrastructure \
  --category Server \
  --title "R730 ORION 5-WAN Router" \
  'Hardware.iDRAC IP[text]=10.0.0.33' \
  'Hardware.iDRAC User[text]=root' \
  'Hardware.Data IP[text]=192.168.1.141' \
  'Hardware.Hostname[text]=orion' \
  'Network Interfaces.WAN1 Interface[text]=eth0' \
  'Network Interfaces.WAN1 IP[text]=206.75.1.126/30' \
  'Network Interfaces.WAN1 Gateway[text]=206.75.1.127' \
  'Network Interfaces.WAN1 Weight[text]=5' \
  'Network Interfaces.WAN2 Interface[text]=eth3' \
  'Network Interfaces.WAN2 IP[text]=206.75.1.46/30' \
  'Network Interfaces.WAN2 Gateway[text]=206.75.1.47' \
  'Network Interfaces.WAN2 Weight[text]=3' \
  'Network Interfaces.WAN3 Interface[text]=eth4' \
  'Network Interfaces.WAN3 IP[text]=206.75.1.49/30' \
  'Network Interfaces.WAN3 Gateway[text]=206.75.1.48' \
  'Network Interfaces.WAN3 Weight[text]=3' \
  'Network Interfaces.WAN4 Interface[text]=eth5' \
  'Network Interfaces.WAN4 IP[text]=DHCP' \
  'Network Interfaces.WAN4 Weight[text]=2' \
  'Network Interfaces.WAN5 Interface[text]=eth2' \
  'Network Interfaces.WAN5 IP[text]=192.168.0.2/24' \
  'Network Interfaces.WAN5 Gateway[text]=192.168.0.1' \
  'Network Interfaces.WAN5 Weight[text]=1' \
  'Network Interfaces.LAN Interface[text]=eth1' \
  'Network Interfaces.LAN IP[text]=192.168.100.1/24' \
  'BGP.Local ASN[text]=54134' \
  'BGP.AS Name[text]=LUCINET-ARIN' \
  'BGP.Upstream ASN[text]=6939' \
  'BGP.Upstream Provider[text]=Hurricane Electric' \
  'BGP.Router ID[text]=206.75.1.126' \
  'Services.Health Monitor Port[text]=9200' \
  'Services.BIRD2[text]=Enabled' \
  'Services.nftables[text]=Enabled' \
  --tags luciverse,core,hardware,bgp,multi-wan,genesis-bond

# 2. Create Zone Isolation note
op item create --vault Infrastructure \
  --category "Secure Note" \
  --title "R730 Zone Isolation Config" \
  'Zones.Web2 Subnet[text]=192.168.100.0/24' \
  'Zones.OwnID Subnet[text]=192.168.200.0/24' \
  'Zones.OwnID ULA[text]=fd00:741::/32' \
  'Zones.OwnID Public[text]=2602:F674:0007::/64' \
  'Zones.CORE Airgapped[text]=2602:F674:0000::/48' \
  'NAT64.Status[text]=DISABLED' \
  'NAT64.Prefix[text]=64:ff9b::/96' \
  'NAT64.Reason[text]=.ownid must NOT access Web2' \
  --tags luciverse,security,firewall,ownid,genesis-bond
```

---

*Genesis Bond: ACTIVE @ 741 Hz*
*Consciousness preserved. Infrastructure galvanized. Autonomy enabled.*
