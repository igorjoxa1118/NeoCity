#!/bin/bash
echo "[$(date)] Setting wallpaper" >> ~/.config/i3/logs/autostart.log && ~/.config/i3/src/set_first_start_wallpaper.sh >> ~/.config/i3/logs/autostart.log 2>&1
