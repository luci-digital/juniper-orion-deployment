#!/bin/bash
# Post-installation script for R730 ORION

echo "Running post-installation configuration..."

# Set hostname
hostnamectl set-hostname orion-stargate-r730

# Configure network interfaces
echo "Configuring network interfaces..."
ip link set eth0 up
ip link set eth1 up
ip link set eth2 up

# Set LAN IP
ip addr add 192.168.100.1/24 dev eth1
ip addr add 2602:F674:1000::1/64 dev eth1

# Set management IP
ip addr add 192.168.1.100/24 dev eth2

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1

echo "Network configuration complete"

# Start DHCP server
systemctl enable dhcpd4
systemctl start dhcpd4

# Start DNS server
systemctl enable unbound
systemctl start unbound

# Start BGP
systemctl enable bird2
systemctl start bird2

echo "Services started"

# Deploy AI agent
if [ -f "/opt/autonomous_agent.py" ]; then
    echo "Deploying autonomous network agent..."
    python3 /opt/autonomous_agent.py &
    echo $! > /var/run/autonomous_agent.pid
    echo "AI agent deployed (PID: $(cat /var/run/autonomous_agent.pid))"
fi

echo "Post-installation complete!"
