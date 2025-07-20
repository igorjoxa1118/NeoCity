#!/bin/bash

if systemctl is-active --quiet bluetooth; then
    echo "󰂯"  # Иконка включенного Bluetooth (Nerd Font)
else
    echo "󰂲"  # Иконка выключенного Bluetooth (Nerd Font)
fi