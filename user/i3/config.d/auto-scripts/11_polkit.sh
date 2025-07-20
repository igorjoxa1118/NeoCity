#!/bin/bash
echo "[$(date)] Starting polkit" >> ~/.config/i3/logs/autostart.log && /usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 >> ~/.config/i3/logs/autostart.log 2>&1
