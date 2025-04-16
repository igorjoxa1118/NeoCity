#!/bin/bash
echo "[$(date)] Starting DBus" >> ~/.config/i3/logs/autostart.log && dbus-update-activation-environment --systemd DISPLAY XAUTHORITY >> ~/.config/i3/logs/autostart.log 2>&1
echo "[$(date)] Starting keyring" >> ~/.config/i3/logs/autostart.log && gnome-keyring-daemon --start --components=pkcs11,secrets,ssh >> ~/.config/i3/logs/autostart.log 2>&1
