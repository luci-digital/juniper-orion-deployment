# NixOS Configuration for Dell R730 CQ5QBM2
# JuniperOrionOS Router Platform

{ config, pkgs, lib, ... }:

{
  imports = [
    ./hardware-configuration.nix
  ];

  # System identity
  networking.hostName = "orion-stargate-r730";
  networking.domain = "lucia-ai.internal";
  system.stateVersion = "24.11";

  # Boot configuration for Dell R730
  boot = {
    loader = {
      systemd-boot.enable = false;
      grub = {
        enable = true;
        devices = [ "/dev/sda" ];
        efiSupport = true;
        efiInstallAsRemovable = true;
      };
    };
    
    # Kernel parameters optimized for R730
    kernelParams = [
      "intel_iommu=on"
      "iommu=pt"
      "default_hugepagesz=1G"
      "hugepagesz=1G"
      "hugepages=32"
      "isolcpus=2-27,30-55"  # Isolate cores for networking
      "nohz_full=2-27,30-55"
      "rcu_nocbs=2-27,30-55"
    ];
    
    # Latest kernel for best network performance
    kernelPackages = pkgs.linuxPackages_latest;
    
    # Kernel modules
    kernelModules = [
      "vfio"
      "vfio_pci"
      "vfio_iommu_type1"
      "bnx2x"  # For Broadcom NICs
      "kvm-intel"
    ];
  };

  # Network configuration
  networking = {
    # Disable NetworkManager for manual control
    networkmanager.enable = false;
    useDHCP = false;
    
    # Enable IPv6
    enableIPv6 = true;
    
    # Interface configuration based on R730 hardware
    interfaces = {
      # WAN - Telus connection (10GbE)
      eth0 = {
        macAddress = "D0:94:66:24:96:7E";
        useDHCP = false;
      };
      
      # LAN - Primary network (10GbE)
      eth1 = {
        ipv4.addresses = [{
          address = "192.168.100.1";
          prefixLength = 24;
        }];
        ipv6.addresses = [{
          address = "2602:F674:1000::1";
          prefixLength = 64;
        }];
        macAddress = "D0:94:66:24:96:80";
      };
      
      # Management interface (1GbE)
      eth2 = {
        ipv4.addresses = [{
          address = "192.168.1.100";
          prefixLength = 24;
        }];
        macAddress = "D0:94:66:24:96:82";
      };
    };
    
    # VLANs for network segmentation
    vlans = {
      vlan10 = {
        id = 10;
        interface = "eth1";
      };
      vlan20 = {
        id = 20;
        interface = "eth1";
      };
    };
    
    # Enable packet forwarding
    firewall.enable = false;  # We'll use nftables directly
    nftables.enable = true;
  };

  # System packages
  environment.systemPackages = with pkgs; [
    # Core utilities
    vim wget curl git htop tmux screen
    
    # Network tools
    tcpdump wireshark-cli nmap iperf3 mtr traceroute
    ethtool iproute2 bridge-utils vlan
    
    # Routing and BGP
    bird2 frr quagga
    
    # VPN
    wireguard-tools openvpn
    
    # Monitoring
    prometheus grafana telegraf
    
    # Container runtime
    docker docker-compose kubernetes
    
    # Development
    python3 go rustc gcc
    
    # Dell specific tools
    ipmitool dmidecode lshw pciutils
  ];
  
  # Enable services
  services = {
    # SSH configuration
    openssh = {
      enable = true;
      settings = {
        PermitRootLogin = "no";
        PasswordAuthentication = false;
      };
    };
    
    # DHCP server for LAN
    dhcpd4 = {
      enable = true;
      interfaces = [ "eth1" ];
      extraConfig = ''
        subnet 192.168.100.0 netmask 255.255.255.0 {
          range 192.168.100.100 192.168.100.200;
          option routers 192.168.100.1;
          option domain-name-servers 192.168.100.1, 8.8.8.8;
          option domain-name "lucia-ai.internal";
        }
      '';
    };
    
    # DNS server
    unbound = {
      enable = true;
      settings = {
        server = {
          interface = [ "192.168.100.1" "::1" ];
          access-control = [ "192.168.100.0/24 allow" ];
        };
      };
    };
    
    # Docker for containerized services
    docker = {
      enable = true;
      storageDriver = "overlay2";
    };
  };
  
  # BGP configuration with BIRD2
  services.bird2 = {
    enable = true;
    config = ''
      router id 100.64.0.1;
      
      # Telus BGP configuration
      protocol bgp telus {
        local as 394955;
        neighbor 206.75.1.127 as 6939;
        
        ipv4 {
          import all;
          export none;
        };
      }
      
      # IPv6 BGP
      protocol bgp he_tunnel {
        local as 394955;
        neighbor 2001:470:0:503::1 as 6939;
        
        ipv6 {
          import all;
          export filter {
            if net ~ 2602:F674::/48 then accept;
            reject;
          };
        };
      }
    '';
  };
}
