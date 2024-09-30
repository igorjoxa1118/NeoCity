#!/bin/bash

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch Polybar
polybar top --config=~/.config/i3/polybar/Tokio_night/config.ini &
#polybar tray --config=~/.config/i3/polybar/Tokio_night/config.ini &
polybar bottom --config=~/.config/i3/polybar/Tokio_night/config.ini &

echo "Polybar launched..."