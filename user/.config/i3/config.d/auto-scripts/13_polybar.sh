#!/bin/bash
echo "[$(date)] Waiting for i3 socket" >> ~/.config/i3/logs/autostart.log && count=0; while [ ! -S "$XDG_RUNTIME_DIR/i3/ipc-socket."* ] && [ $count -lt 20 ]; do sleep 0.1; count=$((count+1)); done; echo "[$(date)] Starting polybar" >> ~/.config/i3/logs/autostart.log && polybar main >> ~/.config/i3/logs/autostart.log 2>&1
