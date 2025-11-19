# 🚀 R730 USB Boot with Callback - Simple Instructions

## ✅ What's Already Done

I've started a **callback server** on your Mac that's listening on port 9999.

When you boot the R730 from USB and run a simple command, it will "knock on my door" and I'll be able to guide the installation!

---

## 📋 Step-by-Step Instructions

### **Step 1: Create Bootable USB (10 minutes)**

**Find your USB drive:**
```bash
diskutil list
```

Look for your USB drive (usually `/dev/disk2` or `/dev/disk3`).

**Create the bootable USB:**

⚠️ **REPLACE `diskX` with your actual disk number!** ⚠️

```bash
# Unmount the USB
diskutil unmountDisk /dev/diskX

# Write the ISO (takes ~10 minutes)
sudo dd if=/tmp/nixos-minimal.iso of=/dev/rdiskX bs=1m status=progress

# Eject when done
diskutil eject /dev/diskX
```

---

### **Step 2: Boot R730 from USB (2 minutes)**

1. **Plug USB** into R730
2. **Reboot** the R730 (or power on if off)
3. **Press F11** during boot to select boot device
4. **Select** the USB drive from the menu
5. **Wait** for NixOS installer to boot (~1 minute)

You'll see a prompt that looks like:
```
nixos@nixos:~$
```

---

### **Step 3: "Knock on My Door" (30 seconds)**

At the NixOS installer prompt, run this **ONE command**:

```bash
    
```

**What happens:**
- This sends a signal to my callback server
- I'll see "✅ R730 NixOS installer is READY!"
- You'll see: "Callback received! Claude is ready to help."

---

### **Step 4: Wait for My Instructions**

Once I see the callback, I'll give you the installation commands to run!

The installation will be:
1. Partition disk (~2 min)
2. Format partitions (~1 min)
3. Mount filesystems (~1 min)
4. Copy our custom config (~2 min)
5. Run `nixos-install` (~15 min)
6. Reboot and configure (~5 min)

**Total: ~30 minutes** of guided installation

---

## 🔍 Troubleshooting

### **If curl command fails:**

The R730 might not have network yet. Try:

```bash
# Get IP via DHCP
dhclient -v eth0

# Wait a moment
sleep 3

# Try callback again
curl http://192.168.1.175:9999/ready
```

### **If still no network:**

Just tell me "I'm at the NixOS prompt but no network" and I'll guide you through manual configuration.

---

## 📊 Current Status

✅ **NixOS ISO ready**: /tmp/nixos-minimal.iso (1.3GB)
✅ **Callback server running**: http://192.168.1.175:9999
✅ **Installation docs ready**: All configs prepared
✅ **Claude ready**: Waiting for your signal!

---

## 🎯 Quick Reference

**Callback URL**: `http://192.168.1.175:9999/ready`

**Callback Command**:
```bash
curl http://192.168.1.175:9999/ready
```

**Alternative (if no network initially)**:
```bash
dhclient -v eth0 && sleep 3 && curl http://192.168.1.175:9999/ready
```

---

**Ready to create the USB? Follow Step 1 above!**

When you're at the NixOS prompt, just run the curl command and I'll see it immediately! 🎉
