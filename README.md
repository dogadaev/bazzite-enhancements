# Bazzite Enhancements

This repository contains scripts and systemd services to optimize a Bazzite Steam Machine setup, focusing on sleep/wake behavior, controller-triggered suspend, and TV power management via ADB.

## Features

### 1. Surgical Wakeup Control
Prevents accidental wakeups from mice, keyboards, or Bluetooth devices, leaving only the controllers as wakeup sources.
- **Logic:** Explicitly disables ACPI wakeup for problematic bridges (e.g., PTXH, GPP0) while keeping CPU USB controllers enabled for 8BitDo receivers.

### 2. TV Power Management (ADB over USB/Network)
Automates turning the Philips TV on/off using ADB commands.
- **Feature:** Automatically detects and prioritizes **ADB over USB** for zero-latency commands, falling back to network ADB if USB is disconnected.

### 3. Controller-Triggered Suspend
Automatically suspends the PC and turns off the TV when 8BitDo controllers are docked.
- **Logic:** Detects when both controllers are in 'Docked' mode, triggers TV-off, waits 5 seconds for HDMI state to settle, then initiates suspend.

## Installation & Configuration

### 1. Local Configuration (Required)
This repository uses a local configuration file to store your specific hardware IDs and network details. This keeps the repository generic and safe for public use.

Create `/etc/bazzite-enhancements.conf` on your Bazzite machine:
```bash
# System User (the user who runs Steam/ADB)
SYSTEM_USER="your_username"

# TV Configuration (Philips Android TV)
TV_IP="192.168.x.x"
TV_HDMI_URI="content://android.media.tv/passthrough/..." # Hardware URI for HDMI Input

# Hardware PCI Addresses (for GPU unbind/bind)
# Find these using `lspci`
GPU_PCI_ADDR="0000:09:00.0"
AUDIO_PCI_ADDR="0000:09:00.1"

# ACPI Wakeup Devices
WAKEUP_DEVICES="PTXH GP12 GPP0 GPP8 SWUS SWDS PT24 PT28 PT29"
CONTROLLER_WAKEUP_DEVICES="XHC0 GP13"
```
*See `config.example` for a template.*

### 2. Deployment
1. Copy scripts to `/usr/local/bin/`:
   ```bash
   sudo cp scripts/*.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/*.sh
   ```
2. Copy the TV script to your local bin:
   ```bash
   mkdir -p ~/.local/bin
   cp scripts/tv-power.py ~/.local/bin/tv-power
   chmod +x ~/.local/bin/tv-power
   ```
3. Install services and udev rules:
   ```bash
   sudo cp services/*.service /etc/systemd/system/
   sudo cp udev-rules/*.rules /etc/udev/rules.d/
   ```
   *Note: Edit `/etc/systemd/system/tv-power-boot.service` and replace `REPLACE_WITH_USER` with your actual Linux username.*

4. Enable services:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable disable-wakeup-triggers.service gpu-unbind.service
   ```

## Hardware Context
- **Motherboard:** Gigabyte B550I AORUS PRO AX (Typical B550 setup)
- **GPU:** AMD Radeon RX 6700 XT (via PCIe Riser)
- **Controllers:** 8BitDo Ultimate 2 Wireless (USB 2.4G)
- **TV:** Philips Android TV (ADB enabled)
