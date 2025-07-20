#!/bin/bash

# Защита от параллельного запуска
LOCK_FILE="/tmp/mpd_total_time.lock"
exec 9>"$LOCK_FILE"
flock -n 9 || exit 1

format_time() {
    printf "%02d:%02d" $(($1/60)) $(($1%60))
}

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
            total=${BASH_REMATCH[2]}
            total_sec=$(awk -F: '{print $1*60+$2}' <<< "$total")
            echo "$(format_time $total_sec)"
        else
            echo "00:00"
        fi
    else
        echo "00:00"
    fi
    
    sleep 1
done

exec 9>&-