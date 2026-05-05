#!/bin/bash
# Triggered by udev on 8BitDo docking events
/usr/bin/systemctl start 8bitdo-suspend.service &
