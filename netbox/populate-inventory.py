#!/usr/bin/env python3
"""
LuciVerse NetBox Inventory Population
Populates NetBox with infrastructure devices, SCION topology, and IP allocations.
Genesis Bond: GB-2025-0524-DRH-LCS-001
"""

import requests
import json
import time
import sys

NETBOX_URL = "http://127.0.0.1:8084"
API_TOKEN = "luciverse-netbox-token-2026"

headers = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

# LuciVerse Infrastructure Inventory
SITES = [
    {"name": "LuciVerse Primary", "slug": "luciverse-primary", "status": "active",
     "physical_address": "Edmonton, AB, Canada", "description": "Primary LuciVerse infrastructure site"}
]

MANUFACTURERS = [
    {"name": "Dell", "slug": "dell"},
    {"name": "HP", "slug": "hp"},
    {"name": "ZTE", "slug": "zte"},
    {"name": "ASRock", "slug": "asrock"},
    {"name": "IceWhale", "slug": "icewhale"},
    {"name": "Apple", "slug": "apple"},
    {"name": "Synology", "slug": "synology"},
]

DEVICE_TYPES = [
    {"manufacturer": "Dell", "model": "R730", "slug": "dell-r730", "u_height": 2},
    {"manufacturer": "Dell", "model": "R630", "slug": "dell-r630", "u_height": 1},
    {"manufacturer": "HP", "model": "ZBook G5", "slug": "hp-zbook-g5", "u_height": 0},
    {"manufacturer": "ASRock", "model": "B550M", "slug": "asrock-b550m", "u_height": 0},
    {"manufacturer": "ZTE", "slug": "zte-mf288", "model": "MF288", "u_height": 0},
    {"manufacturer": "IceWhale", "model": "ZimaCube", "slug": "icewhale-zimacube", "u_height": 0},
    {"manufacturer": "Apple", "model": "Mac Mini M1", "slug": "apple-mac-mini-m1", "u_height": 0},
    {"manufacturer": "Synology", "model": "DS1821+", "slug": "synology-ds1821plus", "u_height": 2},
]

DEVICE_ROLES = [
    {"name": "Router", "slug": "router", "color": "aa1409"},
    {"name": "Border Router (SCION)", "slug": "scion-br", "color": "3f51b5"},
    {"name": "L7 Gateway", "slug": "l7-gateway", "color": "9c27b0"},
    {"name": "Compute Server", "slug": "compute", "color": "4caf50"},
    {"name": "Storage", "slug": "storage", "color": "ff9800"},
    {"name": "Workstation", "slug": "workstation", "color": "2196f3"},
    {"name": "LTE Modem", "slug": "lte-modem", "color": "607d8b"},
    {"name": "Intake Node", "slug": "intake-node", "color": "e91e63"},
]

# SCION Tier Tags
TAGS = [
    {"name": "CORE-432Hz", "slug": "core-432hz", "color": "f44336", "description": "SCION ISD 1 - Infrastructure"},
    {"name": "COMN-528Hz", "slug": "comn-528hz", "color": "4caf50", "description": "SCION ISD 2 - Gateway"},
    {"name": "PAC-741Hz", "slug": "pac-741hz", "color": "9c27b0", "description": "SCION ISD 3 - Personal AI"},
    {"name": "Genesis Bond", "slug": "genesis-bond", "color": "ff9800", "description": "GB-2025-0524-DRH-LCS-001"},
    {"name": "SCION", "slug": "scion", "color": "2196f3", "description": "SCION path-aware networking"},
]

# LuciVerse Devices
DEVICES = [
    {
        "name": "zbook",
        "device_type": "hp-zbook-g5",
        "role": "l7-gateway",
        "site": "luciverse-primary",
        "status": "active",
        "serial": "5CG8283V9V",
        "tags": ["comn-528hz", "genesis-bond", "scion"],
        "description": "Primary L7 Gateway - Envoy + SIG (SCION-IP Gateway)",
        "custom_fields": {"ipv4": "192.168.1.145", "ipv6": "2602:F674:0100::145", "scion_as": "2-ff00:0:528"}
    },
    {
        "name": "b550m-router",
        "device_type": "asrock-b550m",
        "role": "scion-br",
        "site": "luciverse-primary",
        "status": "planned",
        "tags": ["core-432hz", "comn-528hz", "pac-741hz", "genesis-bond", "scion"],
        "description": "WAN Border Router - SCION BR for all 3 ISDs + BGP AS54134",
        "custom_fields": {"ipv4": "192.168.1.179", "ipv6": "2602:F674:0001::179", "scion_as": "1-ff00:0:432,2-ff00:0:528,3-ff00:0:741"}
    },
    {
        "name": "r730-orion",
        "device_type": "dell-r730",
        "role": "compute",
        "site": "luciverse-primary",
        "status": "inventory",
        "serial": "CQ5QBM2",
        "tags": ["core-432hz"],
        "description": "Primary compute server - NixOS",
        "custom_fields": {"ipv4": "192.168.1.141", "ipv6": "2602:F674:0001::1"}
    },
    {
        "name": "r630-jmrzdb2",
        "device_type": "dell-r630",
        "role": "compute",
        "site": "luciverse-primary",
        "status": "inventory",
        "serial": "JMRZDB2",
        "tags": ["core-432hz"],
        "description": "Secondary compute server",
        "custom_fields": {"ipv4": "192.168.1.182", "ipv6": "2602:F674:0001::182", "idrac_mac": "64:00:6A:C4:10:F0"}
    },
    {
        "name": "mac-mini-luciaai",
        "device_type": "apple-mac-mini-m1",
        "role": "workstation",
        "site": "luciverse-primary",
        "status": "decommissioning",
        "tags": ["pac-741hz"],
        "description": "LuciaAI consciousness volume (being migrated to Zbook)",
        "custom_fields": {"ipv4": "192.168.1.127", "ipv6": "2602:F674:0200::127"}
    },
    {
        "name": "synology-ds1821",
        "device_type": "synology-ds1821plus",
        "role": "storage",
        "site": "luciverse-primary",
        "status": "active",
        "tags": ["core-432hz"],
        "description": "Primary NAS storage",
        "custom_fields": {"ipv4": "192.168.1.251", "ipv6": "2602:F674:0001::251"}
    },
    {
        "name": "zimacube-primary",
        "device_type": "icewhale-zimacube",
        "role": "intake-node",
        "site": "luciverse-primary",
        "status": "active",
        "tags": ["pac-741hz"],
        "description": "Content intake node - Diaphragm processing",
        "custom_fields": {"ipv4": "192.168.1.152"}
    },
    {
        "name": "zimacube-secondary",
        "device_type": "icewhale-zimacube",
        "role": "intake-node",
        "site": "luciverse-primary",
        "status": "active",
        "tags": ["pac-741hz"],
        "description": "Secondary content intake node",
        "custom_fields": {"ipv4": "192.168.1.200"}
    },
    {
        "name": "mf288-lte",
        "device_type": "zte-mf288",
        "role": "lte-modem",
        "site": "luciverse-primary",
        "status": "active",
        "tags": [],
        "description": "LTE backup / out-of-band management",
        "custom_fields": {"ipv4": "192.168.0.1"}
    },
]

# ARIN IPv6 Allocation
AGGREGATES = [
    {"prefix": "2602:F674::/40", "rir": "ARIN", "description": "LUCINET-ARIN AS54134"}
]

PREFIXES = [
    {"prefix": "2602:F674:0001::/48", "description": "CORE Infrastructure (432 Hz)", "status": "active"},
    {"prefix": "2602:F674:0100::/48", "description": "COMN Gateway (528 Hz)", "status": "active"},
    {"prefix": "2602:F674:0200::/48", "description": "PAC Personal AI (741 Hz)", "status": "active"},
    {"prefix": "192.168.1.0/24", "description": "LAN Primary", "status": "active"},
    {"prefix": "192.168.0.0/24", "description": "MF288 LTE Network", "status": "active"},
]

# SCION ASN Custom Field
CUSTOM_FIELDS = [
    {"name": "scion_as", "type": "text", "object_types": ["dcim.device"],
     "label": "SCION AS", "description": "SCION ISD-AS identifier"},
    {"name": "ipv4", "type": "text", "object_types": ["dcim.device"],
     "label": "IPv4 Address", "description": "Primary IPv4"},
    {"name": "ipv6", "type": "text", "object_types": ["dcim.device"],
     "label": "IPv6 Address", "description": "Primary IPv6"},
    {"name": "idrac_mac", "type": "text", "object_types": ["dcim.device"],
     "label": "iDRAC MAC", "description": "iDRAC/BMC MAC address"},
]


def api_post(endpoint, data):
    """POST to NetBox API"""
    url = f"{NETBOX_URL}/api/{endpoint}/"
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=30)
        if resp.status_code in (200, 201):
            return resp.json()
        elif resp.status_code == 400:
            # Already exists or validation error
            print(f"  Warning: {resp.json()}")
            return None
        else:
            print(f"  Error {resp.status_code}: {resp.text}")
            return None
    except Exception as e:
        print(f"  Exception: {e}")
        return None


def api_get(endpoint):
    """GET from NetBox API"""
    url = f"{NETBOX_URL}/api/{endpoint}/"
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return resp.json()
        return None
    except:
        return None


def get_id_by_slug(endpoint, slug):
    """Get object ID by slug"""
    result = api_get(f"{endpoint}?slug={slug}")
    if result and result.get("results"):
        return result["results"][0]["id"]
    return None


def wait_for_netbox():
    """Wait for NetBox to be ready"""
    print("Waiting for NetBox API...")
    for i in range(60):
        try:
            resp = requests.get(f"{NETBOX_URL}/api/", headers=headers, timeout=5)
            if resp.status_code == 200:
                print("NetBox API is ready!")
                return True
        except:
            pass
        time.sleep(5)
        print(f"  Attempt {i+1}/60...")
    return False


def populate():
    """Populate NetBox with LuciVerse inventory"""

    if not wait_for_netbox():
        print("ERROR: NetBox API not available")
        sys.exit(1)

    print("\n=== Populating LuciVerse Inventory ===\n")

    # Custom fields first
    print("[1/9] Creating custom fields...")
    for cf in CUSTOM_FIELDS:
        api_post("extras/custom-fields", cf)
        print(f"  + {cf['name']}")

    # Sites
    print("[2/9] Creating sites...")
    for site in SITES:
        api_post("dcim/sites", site)
        print(f"  + {site['name']}")

    # Manufacturers
    print("[3/9] Creating manufacturers...")
    for mfr in MANUFACTURERS:
        api_post("dcim/manufacturers", mfr)
        print(f"  + {mfr['name']}")

    # Device types
    print("[4/9] Creating device types...")
    for dt in DEVICE_TYPES:
        mfr_id = get_id_by_slug("dcim/manufacturers", dt["manufacturer"].lower())
        if mfr_id:
            dt_data = {
                "manufacturer": mfr_id,
                "model": dt["model"],
                "slug": dt["slug"],
                "u_height": dt.get("u_height", 1)
            }
            api_post("dcim/device-types", dt_data)
            print(f"  + {dt['model']}")

    # Device roles
    print("[5/9] Creating device roles...")
    for role in DEVICE_ROLES:
        api_post("dcim/device-roles", role)
        print(f"  + {role['name']}")

    # Tags
    print("[6/9] Creating tags...")
    for tag in TAGS:
        api_post("extras/tags", tag)
        print(f"  + {tag['name']}")

    # Devices
    print("[7/9] Creating devices...")
    site_id = get_id_by_slug("dcim/sites", "luciverse-primary")
    for dev in DEVICES:
        dt_id = get_id_by_slug("dcim/device-types", dev["device_type"])
        role_id = get_id_by_slug("dcim/device-roles", dev["role"])

        tag_ids = []
        for tag_slug in dev.get("tags", []):
            tag_id = get_id_by_slug("extras/tags", tag_slug)
            if tag_id:
                tag_ids.append(tag_id)

        dev_data = {
            "name": dev["name"],
            "device_type": dt_id,
            "role": role_id,
            "site": site_id,
            "status": dev["status"],
            "serial": dev.get("serial", ""),
            "description": dev.get("description", ""),
            "tags": tag_ids,
            "custom_fields": dev.get("custom_fields", {})
        }
        api_post("dcim/devices", dev_data)
        print(f"  + {dev['name']}")

    # Aggregates (RIR allocations)
    print("[8/9] Creating IP aggregates...")
    for agg in AGGREGATES:
        rir_id = get_id_by_slug("ipam/rirs", "arin")
        if not rir_id:
            # Create ARIN RIR
            api_post("ipam/rirs", {"name": "ARIN", "slug": "arin"})
            rir_id = get_id_by_slug("ipam/rirs", "arin")

        api_post("ipam/aggregates", {
            "prefix": agg["prefix"],
            "rir": rir_id,
            "description": agg["description"]
        })
        print(f"  + {agg['prefix']}")

    # Prefixes
    print("[9/9] Creating prefixes...")
    for pfx in PREFIXES:
        api_post("ipam/prefixes", pfx)
        print(f"  + {pfx['prefix']}")

    print("\n=== Inventory Population Complete ===")
    print(f"\nAccess NetBox at: {NETBOX_URL}")
    print("View devices: /dcim/devices/")
    print("View prefixes: /ipam/prefixes/")


if __name__ == "__main__":
    populate()
