#!/bin/bash

# Получаем ID панели (замените на ваш)
POLYBAR_BAR="top"  # Имя вашей панели из конфига

# Получаем координаты модуля i3 (примерные)
# Нужно подобрать значения вручную через xdotool
MODULE_X=100
MODULE_WIDTH=500

while true; do
    # Получаем позицию мыши
    eval $(xdotool getmouselocation --shell)
    
    # Проверяем, находится ли курсор над модулем
    if (( X >= MODULE_X && X <= MODULE_X + MODULE_WIDTH )); then
        # Если да - отправляем сигнал на подсветку
        polybar-msg -p "$(pgrep -f "polybar $POLYBAR_BAR")" hook i3 hover 1
    else
        # Если нет - возвращаем обычный вид
        polybar-msg -p "$(pgrep -f "polybar $POLYBAR_BAR")" hook i3 hover 0
    fi
    
    sleep 0.1
done
