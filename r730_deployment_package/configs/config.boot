#!/bin/vbash
# VyOS Configuration for Dell R730 CQ5QBM2
# JuniperOrionOS Router - Telus Replacement

# System configuration
set system host-name 'orion-r730-router'
set system domain-name 'lucia-ai.internal'
set system time-zone 'America/Edmonton'

# Set login credentials
set system login user admin authentication plaintext-password 'ChangeMe123!'
set system login user admin authentication public-keys admin-key type 'ssh-rsa'
set system login user admin authentication public-keys admin-key key 'AAAAB3NzaC1yc2EAAAADAQABAAAB...'

# Network interfaces based on R730 hardware
# WAN - Connected to Telus (10GbE)
set interfaces ethernet eth0 description 'TELUS-WAN'
set interfaces ethernet eth0 hw-id 'D0:94:66:24:96:7E'
set interfaces ethernet eth0 address 'dhcp'
set interfaces ethernet eth0 dhcpv6-options pd 0 length '48'
set interfaces ethernet eth0 dhcpv6-options pd 0 interface eth1 address '1'
set interfaces ethernet eth0 dhcpv6-options pd 0 interface eth1 sla-id '1'

# LAN - Primary network (10GbE)
set interfaces ethernet eth1 description 'LAN-PRIMARY'
set interfaces ethernet eth1 hw-id 'D0:94:66:24:96:80'
set interfaces ethernet eth1 address '192.168.100.1/24'
set interfaces ethernet eth1 address '2602:F674:1000::1/64'

# Management interface (1GbE)
set interfaces ethernet eth2 description 'MANAGEMENT'
set interfaces ethernet eth2 hw-id 'D0:94:66:24:96:82'
set interfaces ethernet eth2 address '192.168.1.100/24'

# Guest network (1GbE)
set interfaces ethernet eth3 description 'GUEST-NETWORK'
set interfaces ethernet eth3 hw-id 'D0:94:66:24:96:84'
set interfaces ethernet eth3 address '192.168.200.1/24'

# HA interface (10GbE)
set interfaces ethernet eth4 description 'HA-BACKUP'
set interfaces ethernet eth4 hw-id 'D0:94:66:24:96:86'

# DMZ interface (10GbE)
set interfaces ethernet eth5 description 'DMZ'
set interfaces ethernet eth5 hw-id 'D0:94:66:24:96:88'
set interfaces ethernet eth5 address '192.168.50.1/24'

# NAT configuration for IPv4
set nat source rule 100 description 'LAN to WAN'
set nat source rule 100 outbound-interface 'eth0'
set nat source rule 100 source address '192.168.100.0/24'
set nat source rule 100 translation address 'masquerade'

set nat source rule 200 description 'Guest to WAN'
set nat source rule 200 outbound-interface 'eth0'
set nat source rule 200 source address '192.168.200.0/24'
set nat source rule 200 translation address 'masquerade'

# Firewall configuration
set firewall name WAN-IN default-action 'drop'
set firewall name WAN-IN rule 10 action 'accept'
set firewall name WAN-IN rule 10 state established 'enable'
set firewall name WAN-IN rule 10 state related 'enable'
set firewall name WAN-IN rule 20 action 'accept'
set firewall name WAN-IN rule 20 protocol 'icmp'

set firewall name WAN-LOCAL default-action 'drop'
set firewall name WAN-LOCAL rule 10 action 'accept'
set firewall name WAN-LOCAL rule 10 state established 'enable'
set firewall name WAN-LOCAL rule 10 state related 'enable'
set firewall name WAN-LOCAL rule 20 action 'accept'
set firewall name WAN-LOCAL rule 20 protocol 'icmp'
set firewall name WAN-LOCAL rule 30 action 'accept'
set firewall name WAN-LOCAL rule 30 destination port '22'
set firewall name WAN-LOCAL rule 30 protocol 'tcp'
set firewall name WAN-LOCAL rule 30 source address '192.168.1.0/24'

# Apply firewall to interfaces
set interfaces ethernet eth0 firewall in name 'WAN-IN'
set interfaces ethernet eth0 firewall local name 'WAN-LOCAL'

# DHCP server configuration
set service dhcp-server shared-network-name LAN subnet 192.168.100.0/24 default-router '192.168.100.1'
set service dhcp-server shared-network-name LAN subnet 192.168.100.0/24 dns-server '192.168.100.1'
set service dhcp-server shared-network-name LAN subnet 192.168.100.0/24 dns-server '8.8.8.8'
set service dhcp-server shared-network-name LAN subnet 192.168.100.0/24 range 0 start '192.168.100.100'
set service dhcp-server shared-network-name LAN subnet 192.168.100.0/24 range 0 stop '192.168.100.200'
set service dhcp-server shared-network-name LAN subnet 192.168.100.0/24 lease '86400'

set service dhcp-server shared-network-name GUEST subnet 192.168.200.0/24 default-router '192.168.200.1'
set service dhcp-server shared-network-name GUEST subnet 192.168.200.0/24 dns-server '8.8.8.8'
set service dhcp-server shared-network-name GUEST subnet 192.168.200.0/24 range 0 start '192.168.200.100'
set service dhcp-server shared-network-name GUEST subnet 192.168.200.0/24 range 0 stop '192.168.200.200'

# DNS forwarding
set service dns forwarding listen-on 'eth1'
set service dns forwarding listen-on 'eth3'
set service dns forwarding allow-from '192.168.100.0/24'
set service dns forwarding allow-from '192.168.200.0/24'
set service dns forwarding name-server '8.8.8.8'
set service dns forwarding name-server '1.1.1.1'

# BGP configuration for Telus gateways
set protocols bgp 394955 parameters router-id '100.64.0.1'
set protocols bgp 394955 neighbor 206.75.1.127 remote-as '6939'
set protocols bgp 394955 neighbor 206.75.1.127 description 'Telus-Gateway-1'
set protocols bgp 394955 neighbor 206.75.1.47 remote-as '6939'
set protocols bgp 394955 neighbor 206.75.1.47 description 'Telus-Gateway-2'
set protocols bgp 394955 neighbor 206.75.1.48 remote-as '6939'
set protocols bgp 394955 neighbor 206.75.1.48 description 'Telus-Gateway-3'

# IPv6 BGP
set protocols bgp 394955 address-family ipv6-unicast network '2602:F674::/48'

# Static ARP entries for Telus gateways
set protocols static arp 206.75.1.127 hwaddr '74:83:c2:d4:c4:c9'
set protocols static arp 206.75.1.47 hwaddr '78:8a:20:7d:a3:91'
set protocols static arp 206.75.1.48 hwaddr '74:83:c2:d4:d3:8a'

# System services
set service ssh port '22'
set service ssh listen-address '192.168.100.1'
set service ssh listen-address '192.168.1.100'

# Commit configuration
commit
save
