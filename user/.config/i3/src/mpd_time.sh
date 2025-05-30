#!/bin/bash

format_time() {
    printf "%02d:%02d" $(($1/60)) $(($1%60))
}

while true; do
    if status=$(mpc status 2>/dev/null); then
        if echo "$status" | grep -q 'playing\|paused'; then
            # Получаем информацию о времени
            time_data=$(mpc status | awk '/\[/ {print $3}')
            elapsed=$(echo "$time_data" | cut -d'/' -f1)
            total=$(echo "$time_data" | cut -d'/' -f2)
            
            # Конвертация в секунды
            elapsed_sec=$(echo "$elapsed" | awk -F: '{print $1*60+$2}')
            total_sec=$(echo "$total" | awk -F: '{print $1*60+$2}')
            
            # Вычисление оставшегося времени
            remaining_sec=$((total_sec - elapsed_sec))
            
            # Форматированный вывод
            if [ "$remaining_sec" -ge 0 ]; then
                echo "[$(format_time $total_sec)]:[-$(format_time $remaining_sec)]"
            else
                echo "[$(format_time $total_sec)]:[00:00]"
            fi
        else
            echo "[00:00]:[00:00]"
        fi
    else
        echo "MPD Offline"
    fi
    sleep 1
done