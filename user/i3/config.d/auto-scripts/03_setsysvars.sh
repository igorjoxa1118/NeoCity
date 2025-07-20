#!/bin/bash
echo "[$(date)] Running SetSysVars" >> ~/.config/i3/logs/autostart.log
~/.config/i3/src/SetSysVars >> ~/.config/i3/logs/autostart.log 2>&1