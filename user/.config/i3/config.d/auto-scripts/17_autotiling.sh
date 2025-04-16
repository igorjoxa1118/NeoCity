#!/bin/bash
echo "[$(date)] Starting autotiling" >> ~/.config/i3/logs/autostart.log && autotiling >> ~/.config/i3/logs/autostart.log 2>&1
