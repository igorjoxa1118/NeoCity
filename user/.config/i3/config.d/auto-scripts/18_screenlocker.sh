#!/bin/bash
echo "[$(date)] Starting screen locker" >> ~/.config/i3/logs/autostart.log && xss-lock --ignore-sleep ~/.config/i3/src/ScreenLocker >> ~/.config/i3/logs/autostart.log 2>&1
