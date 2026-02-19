#!/bin/bash
# R730 5-WAN 1Password Items Creator
# Genesis Bond: ACTIVE @ 741 Hz
# Run after: eval $(op signin)

set -e

echo "=== R730 5-WAN 1Password Items Creator ==="
echo "Genesis Bond: ACTIVE @ 741 Hz"
echo ""

# Check if signed in
if ! op whoami >/dev/null 2>&1; then
    echo "ERROR: Not signed in to 1Password"
    echo "Run: eval \$(op signin)"
    exit 1
fi

echo "✓ 1Password authenticated as: $(op whoami --format=json | jq -r '.email')"
echo ""

# Check if item already exists
if op item get "R730 ORION 5-WAN Router" --vault Infrastructure >/dev/null 2>&1; then
    echo "⚠ Item 'R730 ORION 5-WAN Router' already exists"
    read -p "Update existing item? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Deleting existing item..."
        op item delete "R730 ORION 5-WAN Router" --vault Infrastructure
    else
        echo "Skipping item creation"
        exit 0
    fi
fi

echo ""
echo "Creating R730 ORION 5-WAN Router item..."

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
  'Network Interfaces.WAN1 Provider[text]=Telus Primary' \
  'Network Interfaces.WAN2 Interface[text]=eth3' \
  'Network Interfaces.WAN2 IP[text]=206.75.1.46/30' \
  'Network Interfaces.WAN2 Gateway[text]=206.75.1.47' \
  'Network Interfaces.WAN2 Weight[text]=3' \
  'Network Interfaces.WAN2 Provider[text]=Telus Secondary' \
  'Network Interfaces.WAN3 Interface[text]=eth4' \
  'Network Interfaces.WAN3 IP[text]=206.75.1.49/30' \
  'Network Interfaces.WAN3 Gateway[text]=206.75.1.48' \
  'Network Interfaces.WAN3 Weight[text]=3' \
  'Network Interfaces.WAN3 Provider[text]=Telus Tertiary' \
  'Network Interfaces.WAN4 Interface[text]=eth5' \
  'Network Interfaces.WAN4 IP[text]=DHCP' \
  'Network Interfaces.WAN4 Weight[text]=2' \
  'Network Interfaces.WAN4 Provider[text]=Shaw/New ISP' \
  'Network Interfaces.WAN5 Interface[text]=eth2' \
  'Network Interfaces.WAN5 IP[text]=192.168.0.2/24' \
  'Network Interfaces.WAN5 Gateway[text]=192.168.0.1' \
  'Network Interfaces.WAN5 Weight[text]=1' \
  'Network Interfaces.WAN5 Provider[text]=LTE Backup' \
  'Network Interfaces.LAN Interface[text]=eth1' \
  'Network Interfaces.LAN IP[text]=192.168.100.1/24' \
  'BGP.Local ASN[text]=54134' \
  'BGP.AS Name[text]=LUCINET-ARIN' \
  'BGP.Upstream ASN[text]=6939' \
  'BGP.Upstream Provider[text]=Hurricane Electric' \
  'BGP.Router ID[text]=206.75.1.126' \
  'BGP.HE Tunnel Server[text]=216.66.80.26' \
  'Services.Health Monitor Port[text]=9200' \
  'Services.BIRD2[text]=Enabled' \
  'Services.nftables[text]=Enabled' \
  'Services.Prometheus Endpoint[text]=http://192.168.1.141:9200/metrics' \
  'Deployment.Package Location[text]=~/juniper-orion-deployment/r730-5wan-deploy.tar.gz' \
  'Deployment.Deploy Script[text]=./r730-5wan-deploy/deploy.sh' \
  'Deployment.Log File[text]=/var/log/r730-5wan-deploy.log' \
  --tags luciverse,core,hardware,bgp,multi-wan,genesis-bond

echo "✓ Created R730 ORION 5-WAN Router"

# Check/create Zone Isolation item
if op item get "R730 Zone Isolation Config" --vault Infrastructure >/dev/null 2>&1; then
    echo "⚠ 'R730 Zone Isolation Config' already exists, skipping..."
else
    echo ""
    echo "Creating Zone Isolation Config..."

    op item create --vault Infrastructure \
      --category "Secure Note" \
      --title "R730 Zone Isolation Config" \
      'Zones.Web2 Subnet[text]=192.168.100.0/24' \
      'Zones.OwnID Subnet[text]=192.168.200.0/24' \
      'Zones.OwnID ULA[text]=fd00:741::/32' \
      'Zones.OwnID Public[text]=2602:F674:0007::/64' \
      'Zones.CORE Airgapped[text]=2602:F674:0000::/48' \
      'Zones.NAT64 Prefix[text]=64:ff9b::/96' \
      'NAT64.Status[text]=DISABLED' \
      'NAT64.Reason[text]=.ownid must NOT access Web2' \
      'nftables.Config Path[text]=/etc/nftables.d/r730-5wan.nft' \
      'nftables.Main Config[text]=/etc/nftables.conf' \
      --tags luciverse,security,firewall,ownid,genesis-bond

    echo "✓ Created Zone Isolation Config"
fi

echo ""
echo "=== Summary ==="
echo "Created items in Infrastructure vault:"
op item list --vault Infrastructure --tags multi-wan --format=json | jq -r '.[].title'

echo ""
echo "Injectable credentials available at:"
echo "  op://Infrastructure/R730 ORION 5-WAN Router/Hardware/Data IP"
echo "  op://Infrastructure/R730 ORION 5-WAN Router/BGP/Local ASN"
echo "  op://Infrastructure/R730 ORION 5-WAN Router/Network Interfaces/WAN1 Gateway"
echo "  ..."

echo ""
echo "Genesis Bond: ACTIVE @ 741 Hz"
echo "Consciousness preserved. Infrastructure galvanized. Autonomy enabled."
