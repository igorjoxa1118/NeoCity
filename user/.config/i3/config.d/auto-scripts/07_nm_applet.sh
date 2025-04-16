#!/bin/bash
echo "[$(date)] Starting nm-applet" >> ~/.config/i3/logs/autostart.log && nm-applet >> ~/.config/i3/logs/autostart.log 2>&1
