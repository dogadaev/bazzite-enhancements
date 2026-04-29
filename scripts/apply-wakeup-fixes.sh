#!/bin/bash
# Load configuration
[ -f /etc/bazzite-enhancements.conf ] && . /etc/bazzite-enhancements.conf

# Disable ACPI wakeup for problematic devices
for dev in ${WAKEUP_DEVICES:-PTXH GP12 GPP0 GPP8 SWUS SWDS PT24 PT28 PT29}; do
    if grep -q "^$dev.*enabled" /proc/acpi/wakeup; then
        echo "$dev" > /proc/acpi/wakeup
    fi
done

# Enable ACPI wakeup for controllers
for dev in ${CONTROLLER_WAKEUP_DEVICES:-XHC0 GP13}; do
    if grep -q "^$dev.*disabled" /proc/acpi/wakeup; then
        echo "$dev" > /proc/acpi/wakeup
    fi
done

# USB Hubs
for hub in /sys/bus/usb/devices/usb*; do
    [ -f "$hub/power/wakeup" ] || continue
    if echo "$hub" | grep -q "usb3\|usb4"; then
        echo enabled > "$hub/power/wakeup"
    else
        echo disabled > "$hub/power/wakeup"
    fi
done
