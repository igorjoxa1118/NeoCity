#!/bin/bash
echo "[$(date)] Starting power manager" >> ~/.config/i3/logs/autostart.log && export SESSION_MANAGER="" && xfce4-power-manager >> ~/.config/i3/logs/autostart.log 2>&1