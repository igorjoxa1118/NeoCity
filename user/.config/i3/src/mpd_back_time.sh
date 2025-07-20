#!/bin/bash

# Защита от параллельного запуска
LOCK_FILE="/tmp/mpd_back_time.lock"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 1

format_time() {
    printf "%02d:%02d" $(($1/60)) $(($1%60))
}

handle_scroll() {
    case $1 in
        "up") mpc seek +5 >/dev/null 2>&1 ;;
        "down") mpc seek -5 >/dev/null 2>&1 ;;
    esac
}

# Обработка аргументов
if [ "$1" = "--scroll" ] && [ -n "$2" ]; then
    handle_scroll "$2"
    exit 0
fi

safe_mpc() {
    mpc status 2>/dev/null || echo "MPD Offline"
}

while true; do
    status=$(safe_mpc)
    
    if [[ "$status" == "MPD Offline" ]]; then
        echo "MPD Offline"
        sleep 1
        continue
    fi

    if grep -q 'playing\|paused' <<< "$status"; then
        time_data=$(awk '/\[/ {print $3}' <<< "$status")
        
        # Проверка корректности формата времени
        if [[ "$time_data" =~ ([0-9]+:[0-9]+)/([0-9]+:[0-9]+) ]]; then
            elapsed=${BASH_REMATCH[1]}
            total=${BASH_REMATCH[2]}
            
            elapsed_sec=$(awk -F: '{print $1*60+$2}' <<< "$elapsed")
            total_sec=$(awk -F: '{print $1*60+$2}' <<< "$total")
            
            remaining_sec=$((total_sec - elapsed_sec))
            
            if [ "$remaining_sec" -ge 0 ]; then
                echo "-$(format_time $remaining_sec)"
            else
                echo "00:00"
            fi
        else
            echo "00:00"
        fi
    else
        echo "00:00"
    fi
    
    sleep 1
done

exec 9>&-