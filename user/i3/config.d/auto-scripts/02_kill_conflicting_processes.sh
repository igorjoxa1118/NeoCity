#!/bin/bash
echo '[$(date)] Killing conflicting processes' >> ~/.config/i3/logs/autostart.log && pkill picom || true; pkill xsettingsd || true; pkill xscreensaver || true; pkill gnome-keyring-daemon || true; pkill polybar || true
