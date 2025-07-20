#!/bin/bash
echo "[$(date)] Running SetUser" >> ~/.config/i3/logs/autostart.log
~/.config/i3/src/SetUser >> ~/.config/i3/logs/autostart.log 2>&1