#!/bin/bash
echo "[$(date)] Starting picom" >> ~/.config/i3/logs/autostart.log && picom -b --config "$HOME/.config/i3/config.d/picom.conf" >> ~/.config/i3/logs/autostart.log 2>&1 || echo "[ERROR] Failed to start picom" >> ~/.config/i3/logs/autostart.log
