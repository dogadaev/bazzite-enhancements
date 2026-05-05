#!/usr/bin/env python3
import os
import shutil
import socket
import subprocess
import sys
import time

# Load configuration from /etc/bazzite-enhancements.conf
CONFIG_PATH = "/etc/bazzite-enhancements.conf"
config = {}

if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, "r") as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                config[key] = val.strip('"')

# Default values if config is missing
HOST = config.get("TV_IP", "192.168.1.100")
MACS = config.get("TV_MACS", "").split()

# Get SYSTEM_USER safely
SYSTEM_USER = config.get("SYSTEM_USER")
if not SYSTEM_USER:
    try:
        SYSTEM_USER = os.getlogin()
    except Exception:
        SYSTEM_USER = os.environ.get("USER") or os.environ.get("LOGNAME") or "dogad"

HDMI3_URI = config.get("TV_HDMI_URI", "content://android.media.tv/passthrough/com.mediatek.tvinput%2F.hdmi.HDMIInputService%2FHW7")

LOG_FILE = "/tmp/tv-power.log"

def log(msg):
    # Print to stdout/journal
    print(msg, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"{time.ctime()}: {msg}\n")
    except Exception:
        pass

def send_wol(macs):
    if not macs:
        return
    log(f"Sending WOL packets to {macs}")
    for mac in macs:
        try:
            mac_clean = mac.replace(":", "").replace("-", "")
            data = bytes.fromhex("ff" * 6 + mac_clean * 16)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.sendto(data, ("<broadcast>", 9))
                s.sendto(data, ("255.255.255.255", 9))
        except Exception as e:
            log(f"WOL error for {mac}: {e}")

# Use a more robust way to find ADB in user home or system
def find_adb():
    # Try common Bazzite/Fedora Silverblue home paths
    home_paths = [
        os.path.expanduser(f"~{SYSTEM_USER}"),
        f"/home/{SYSTEM_USER}",
        f"/var/home/{SYSTEM_USER}"
    ]
    for home in home_paths:
        adb_path = os.path.join(home, ".local/bin/adb")
        if os.path.exists(adb_path):
            return adb_path
    return shutil.which("adb") or os.path.expanduser("~/.local/bin/adb")

ADB = find_adb()

def get_adb_target():
    try:
        output = subprocess.check_output([ADB, "devices"], text=True)
        lines = [l for l in output.splitlines() if l.endswith("\tdevice")]
        if lines:
            for line in lines:
                serial = line.split()[0]
                if serial != f"{HOST}:5555":
                    return serial
            return lines[0].split()[0]
    except Exception:
        pass
    return f"{HOST}:5555"

ADB_TARGET = get_adb_target()

def run_adb(cmd):
    return os.system(f"{ADB} -s {ADB_TARGET} {cmd} > /dev/null 2>&1")

def adb_output(*args):
    try:
        return subprocess.check_output([ADB, "-s", ADB_TARGET, *args], text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return ""

def connect_adb(timeout_s=90):
    if ":" not in ADB_TARGET:
        return True 
    
    # First, try to see if it's already connected
    if "device" in adb_output("get-state"):
        return True

    log(f"Attempting to connect to {ADB_TARGET} (Timeout: {timeout_s}s)")
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        # Try connecting
        os.system(f"timeout 3 {ADB} connect {ADB_TARGET} > /dev/null 2>&1")
        # Check state
        state = adb_output("get-state")
        if "device" in state:
            log(f"Connected to {ADB_TARGET}")
            return True
        time.sleep(2)
    return False

def turn_off():
    log(f"Turning off TV (Target: {ADB_TARGET})")
    if connect_adb(timeout_s=10):
        run_adb("shell input keyevent KEYCODE_SLEEP")
        log("Sent KEYCODE_SLEEP")
    else:
        log("Failed to connect to ADB for turn_off")
    return 0

def turn_on():
    log(f"Initiating TV Wake Sequence (Target: {ADB_TARGET})")
    
    # 1. Send WOL to wake the NIC
    send_wol(MACS)
    
    # 2. Wait for ADB connection
    if not connect_adb(timeout_s=60): 
        log("Failed to connect to ADB for turn_on after 60s")
        return 1
    
    # 3. Wake up the screen
    run_adb("shell input keyevent KEYCODE_WAKEUP")
    log("Sent KEYCODE_WAKEUP")
    
    # Give the TV a moment to process the wake
    time.sleep(5)
    
    # Fallback power toggle if still not awake
    if "Awake" not in adb_output("shell", "dumpsys", "power"):
        run_adb("shell input keyevent KEYCODE_POWER")
        log("Sent KEYCODE_POWER (fallback)")
        time.sleep(5)
    
    # 4. Switch to HDMI and hold it
    # We switch twice with a delay to ensure it 'sticks' even if CEC tries to fight it
    def switch_input():
        log(f"Switching to HDMI input: {HDMI3_URI}")
        run_adb(f"shell am start -W -n org.droidtv.playtv/.PlayTvActivity -a android.intent.action.VIEW -d {HDMI3_URI}")

    switch_input()
    time.sleep(10) # Wait for TV to fully settle
    switch_input() # Re-send to ensure we stay on HDMI3
    
    log("Wake sequence completed")
    return 0

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "on"
    if cmd == "on": sys.exit(turn_on())
    else: sys.exit(turn_off())
