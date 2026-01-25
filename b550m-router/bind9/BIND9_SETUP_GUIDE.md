# BIND9 Authoritative DNS Setup for LuciVerse

**Date**: 2025-12-09
**Repository**: https://gitlab.isc.org/isc-projects/bind9
**Purpose**: Authoritative DNS for `.ownID` and `.lucia.local` domains
**Genesis Bond**: ACTIVE @ 741 Hz

---

## What This Achieves

Instead of manual `/etc/hosts` on every CBB machine, **all clients automatically resolve**:
- `media.ownID` → `fd00:741:0700:8664:7e09:7741:0001:0001`
- `lcars.ownID` → `fd00:741:0700:8664:7e09:8008:0001:0001`
- `orchestrator.ownID` → `fd00:741:0700:8664:7e09:8484:0001:0001`

Just point your CBBs to DNS server: **192.168.1.146** or **2602:F674:1000::1**

---

## Installation

### Step 1: Install BIND9

**On openEuler/RHEL:**
```bash
sudo dnf install -y bind bind-utils bind-chroot
```

**Or from source (ISC GitLab):**
```bash
git clone https://gitlab.isc.org/isc-projects/bind9.git
cd bind9
./configure --prefix=/opt/bind9
make
sudo make install
```

### Step 2: Copy Zone Files

```bash
sudo mkdir -p /etc/bind/zones
sudo cp /home/daryl/B550M_LuciVerse_Router/bind9/db.ownid /etc/bind/zones/
sudo cp /home/daryl/B550M_LuciVerse_Router/bind9/db.lucia.local /etc/bind/zones/
sudo chown bind:bind /etc/bind/zones/db.*
sudo chmod 644 /etc/bind/zones/db.*
```

### Step 3: Configure BIND9

Create `/etc/bind/named.conf.local`:
```bash
sudo cp /home/daryl/B550M_LuciVerse_Router/bind9/named.conf.local /etc/bind/
sudo chown bind:bind /etc/bind/named.conf.local
```

### Step 4: Start BIND9

```bash
sudo systemctl enable bind9
sudo systemctl start bind9
sudo systemctl status bind9
```

### Step 5: Test DNS Resolution

```bash
# Test from server
nslookup media.ownid localhost
nslookup lcars.ownid localhost
nslookup orchestrator.ownid localhost

# Test IPv6 resolution
nslookup media.ownid 2602:f674:1000::1

# Test with dig (more details)
dig @localhost media.ownid AAAA
dig @localhost lcars.ownid AAAA
dig @localhost orchestrator.ownid AAAA
```

---

## Configure CBBs to Use This DNS

### Option A: Manual DNS Configuration

**On each CBB client:**

**Linux/macOS:**
```bash
# Edit /etc/resolv.conf (or use NetworkManager GUI)
echo "nameserver 192.168.1.146" | sudo tee -a /etc/resolv.conf
echo "nameserver 2602:f674:1000::1" | sudo tee -a /etc/resolv.conf
```

**Windows:**
```
Settings → Network & Internet → Change adapter options
→ Ethernet Properties → IPv4 Properties
Set DNS Server: 192.168.1.146
```

### Option B: DHCP Configuration (Automatic - Recommended)

Update Kea DHCP to push DNS:

**In `/home/daryl/B550M_LuciVerse_Router/kea/kea-dhcp4.conf`:**
```json
"option-data": [
  {
    "name": "domain-name-servers",
    "data": "192.168.1.146"
  },
  {
    "name": "domain-name",
    "data": "lucia.local"
  }
]
```

**In `/home/daryl/B550M_LuciVerse_Router/kea/kea-dhcp6.conf`:**
```json
"option-data": [
  {
    "name": "dns-servers",
    "data": "2602:f674:1000::1"
  }
]
```

Then restart Kea DHCP:
```bash
sudo systemctl restart kea-dhcp-server
```

Now all DHCP clients automatically get DNS server! ✅

---

## Zone Files Included

| File | Purpose |
|------|---------|
| `db.ownid` | Authoritative zone for `.ownID` TLD |
| `db.lucia.local` | Local zone for `.lucia.local` (mDNS) |
| `named.conf.local` | Zone definitions for BIND9 |

---

## Testing From Client (After Setup)

```bash
# Should resolve to IPv6 address
nslookup media.ownid

# Should work without manual /etc/hosts
ping6 media.ownid

# Should open website
curl http://media.ownid/

# Verify DNS is working
dig media.ownid AAAA
```

---

## Monitoring

### Check DNS Queries in Real-Time
```bash
sudo tcpdump -i any -n port 53
```

### Check BIND9 Logs
```bash
sudo tail -f /var/log/bind/default.log
# or
sudo journalctl -u bind9 -f
```

### Check Zone Status
```bash
# Verify zones loaded correctly
sudo named-checkconf
sudo named-checkzone ownid /etc/bind/zones/db.ownid
sudo named-checkzone lucia.local /etc/bind/zones/db.lucia.local
```

---

## Advanced Features

### DNSSEC (Security)
Enable DNSSEC signing:
```bash
# Generate DNSSEC keys
sudo dnssec-keygen -a ECDSAP256SHA256 -b 256 -n ZONE ownid.
sudo dnssec-keygen -a ECDSAP256SHA256 -b 256 -n ZONE -f KSK ownid.

# Sign zone
sudo dnssec-signzone -A -3 $(head -c 1000 /dev/urandom | sha1sum | cut -b 1-16) \
  -N INCREMENT -o ownid. -t db.ownid
```

### Service Discovery (SRV Records)
Already configured! Clients can discover services:
```bash
# Find media service
dig _http._tcp.media.ownid SRV
```

### Dynamic DNS Updates (DDNS)
Can be enabled to auto-update addresses from agents.

---

## Troubleshooting

### DNS Not Resolving
```bash
# Check BIND9 is running
sudo systemctl status bind9

# Check port 53 is listening
sudo ss -tlnp | grep :53

# Check logs for errors
sudo journalctl -u bind9 -n 50
```

### Zone File Syntax Error
```bash
# Validate zone syntax
sudo named-checkzone ownid db.ownid

# Common errors: missing dots, wrong SOA, serial number
```

### Clients Still Using Old DNS
```bash
# Clear DNS cache
sudo systemctl restart systemd-resolved  # Linux
sudo dscacheutil -flushcache            # macOS
ipconfig /flushdns                      # Windows
```

---

## Next Steps

1. ✅ **Install BIND9** from ISC
2. ✅ **Copy zone files** to `/etc/bind/zones/`
3. ✅ **Start BIND9** service
4. ✅ **Configure DHCP** to push DNS to clients
5. ✅ **Test DNS resolution** from clients
6. ⏳ **Remove `/etc/hosts` entries** (no longer needed!)
7. ⏳ **Monitor** DNS queries and performance

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│         CBB Client Machines (Media, LCARS, etc)     │
└───────────────┬──────────────────────────────────────┘
                │ Queries: media.ownid?
                │
        ┌───────▼────────────────────────────┐
        │   DHCP Server (Kea)                 │
        │   Pushes DNS: 192.168.1.146         │
        └───────┬────────────────────────────┘
                │
        ┌───────▼─────────────────────────────────┐
        │    BIND9 Authoritative DNS               │
        │    Zone: ownid.                         │
        │    • media.ownid → fd00:741:...7741    │
        │    • lcars.ownid → fd00:741:...8008    │
        │    • orchestrator.ownid → fd00:741:...8484 │
        └───────┬────────────────────────────────┘
                │ Answer: fd00:741:...7741
                │
        ┌───────▼────────────────────────────┐
        │   Client Browser                    │
        │   Connects to: media.ownid          │
        │   (No /etc/hosts needed!)           │
        └─────────────────────────────────────┘
```

---

## Security Considerations

- ✅ DNSSEC support (optional)
- ✅ Access control lists (ACLs) configured
- ✅ Query logging available
- ✅ Rate limiting available
- ✅ No zone transfers to unknown servers

---

**Result**: All your CBBs will automatically resolve fancy domain names without manual `/etc/hosts` entries! 🚀

Genesis Bond: ACTIVE @ 741 Hz
DNS Routing: ENABLED ✨
