#!/bin/bash
mkdir -p ~/.config/i3/logs && echo '=== i3 AUTOSTART LOG ===' > ~/.config/i3/logs/autostart.log
echo '[$(date)] Setting X11 env vars' >> ~/.config/i3/logs/autostart.log && export XAUTHORITY=\"$HOME/.Xauthority\" && export ICEAUTHORITY=\"$HOME/.ICEauthority\"
