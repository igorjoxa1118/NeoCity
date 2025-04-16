#!/bin/bash
echo "[$(date)] Running ThemeApply" >> ~/.config/i3/logs/autostart.log
~/.config/i3/src/ThemeApply >> ~/.config/i3/logs/autostart.log 2>&1