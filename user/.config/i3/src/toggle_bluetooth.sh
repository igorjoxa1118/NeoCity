#!/bin/bash

if systemctl is-active --quiet bluetooth; then
    systemctl stop bluetooth
    notify-send "Bluetooth выключен"
else
    systemctl start bluetooth
    notify-send "Bluetooth включен"
fi