#!/bin/bash
echo "[$(date)] Starting audio effects" >> ~/.config/i3/logs/autostart.log && export GTK_THEME=catppuccin-mocha && /usr/bin/nohup /usr/bin/easyeffects --gapplication-service >> ~/.config/i3/logs/autostart.log 2>&1
