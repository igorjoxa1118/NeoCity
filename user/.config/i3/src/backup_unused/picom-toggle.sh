#!/bin/bash
CONFIG_PATH="$HOME/.config/i3/config.d/picom.conf"

if pgrep -x "picom" > /dev/null; then
    notify-send "Picom" "Compositor остановлен"
    killall picom
else
    if picom -b --config "$CONFIG_PATH" --backend glx --vsync; then
        notify-send "Picom" "Compositor запущен"
    else
        notify-send "Picom" "Ошибка запуска, пробую xrender..."
        picom -b --config "$CONFIG_PATH" --backend xrender --vsync
    fi
fi