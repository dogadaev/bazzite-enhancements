#!/bin/sh
[ -f /etc/bazzite-enhancements.conf ] && . /etc/bazzite-enhancements.conf

GPU_PCI="${GPU_PCI_ADDR:-0000:09:00.0}"
AUDIO_PCI="${AUDIO_PCI_ADDR:-0000:09:00.1}"
USER_NAME="${SYSTEM_USER:-dogad}"

if [ "$1" = "pre" ]; then
    echo "$GPU_PCI" > /sys/bus/pci/drivers/amdgpu/unbind
elif [ "$1" = "post" ]; then
    echo "$GPU_PCI" > /sys/bus/pci/drivers/amdgpu/bind
    (
        sleep 1
        # Refresh ADB and turn on TV
        /usr/sbin/runuser -l "$USER_NAME" -c 'adb kill-server; /usr/bin/python3 ~/.local/bin/tv-power on'
    ) &
fi
