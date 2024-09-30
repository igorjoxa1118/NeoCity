#!/bin/bash

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch Polybar, using default config location ~/Документы/dotfiles/config/polybar/config
polybar main --config=~/Документы/dotfiles/config/polybar/config.ini &
polybar three --config=~/Документы/dotfiles/config/polybar/config.ini &

echo "Polybar launched..."