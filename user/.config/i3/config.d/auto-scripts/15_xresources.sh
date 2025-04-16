#!/bin/bash
echo "[$(date)] Loading Xresources" >> ~/.config/i3/logs/autostart.log && xrdb -load "$HOME/.Xresources" >> ~/.config/i3/logs/autostart.log 2>&1
