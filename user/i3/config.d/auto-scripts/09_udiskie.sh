#!/bin/bash
echo "[$(date)] Starting udiskie" >> ~/.config/i3/logs/autostart.log && udiskie -t >> ~/.config/i3/logs/autostart.log 2>&1
