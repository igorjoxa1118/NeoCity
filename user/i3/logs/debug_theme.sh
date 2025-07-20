#!/bin/bash

# Диагностика темы
echo "=== Текущая тема ==="
cat ~/.config/i3/config.d/.rice
echo -e "\n=== GTK настройки ==="
gsettings get org.gnome.desktop.interface gtk-theme
echo -e "\n=== Запущенные процессы Thunar ==="
pgrep -a thunar
echo -e "\n=== Окна Thunar ==="
xdotool search --class thunar | while read id; do
    echo "Window $id:"
    xprop -id $id | grep GTK_THEME
done
echo -e "\n=== Xsettingsd ==="
pgrep -a xsettingsd
cat ~/.xsettingsd