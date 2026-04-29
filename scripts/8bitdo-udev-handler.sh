#!/bin/bash
# Triggered by udev on 8BitDo docking events
[ -f /etc/bazzite-enhancements.conf ] && . /etc/bazzite-enhancements.conf

LOG="/tmp/8bitdo-udev.log"
echo "$(date): Event triggered" >> "$LOG"

# Wait for the USB bus to settle
sleep 2

# Check if any controller is still in 'Active' mode (6012)
if ! /usr/bin/lsusb -d 2dc8:6012 > /dev/null; then
    # Check if at least one is in 'Docked' mode (6013)
    if /usr/bin/lsusb -d 2dc8:6013 > /dev/null; then
        echo "$(date): All controllers docked. Turning off TV and Suspending..." >> "$LOG"
        
        # Turn off TV as configured user
        /usr/sbin/runuser -l "${SYSTEM_USER:-dogad}" -c "/usr/bin/python3 /home/${SYSTEM_USER:-dogad}/.local/bin/tv-power off"
        
        # Buffer to allow TV to fully turn off and HDMI state to settle
        echo "$(date): Waiting for TV to settle..." >> "$LOG"
        sleep 5
        
        echo "$(date): Triggering systemctl suspend" >> "$LOG"
        /usr/bin/systemctl suspend
    fi
fi
