#!/bin/bash

# Проверка на уже запущенный экземпляр
LOCK_FILE="/tmp/cava.lock"
if [ -f "$LOCK_FILE" ]; then
    if ps -p $(cat "$LOCK_FILE") >/dev/null 2>&1; then
        echo "Another instance is already running. Exiting." >&2
        exit 1
    else
        rm "$LOCK_FILE"
    fi
fi
echo $$ > "$LOCK_FILE"

# Конфигурационный файл
CONFIG_FILE="/tmp/cava_config_$$"
cat >"$CONFIG_FILE" <<'EOF'
[general]
bars = 15
framerate = 25
sensitivity = 100

[input]
method = pulse
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7

[color]
gradient = 0

[smoothing]
integral = 100
gravity = 100
EOF

# Цветовая схема Catppuccin
COLORS=("#89b4fa" "#f38ba8" "#fab387" "#a6e3a1" "#94e2d5" 
        "#74c7ec" "#cba6f7" "#f5e0dc" "#89b4fa" "#f38ba8"
        "#fab387" "#a6e3a1" "#94e2d5" "#74c7ec" "#cba6f7")

# Очистка при завершении
cleanup() {
    rm -f "$CONFIG_FILE" "$LOCK_FILE"
    [ -n "$CAVA_PID" ] && kill "$CAVA_PID" 2>/dev/null
    exit 0
}
trap cleanup EXIT TERM INT

# Запуск CAVA
cava -p "$CONFIG_FILE" | {
    LAST_SOUND=$(date +%s)
    SOUND_TIMEOUT=2
    DEFAULT_MODE=true

    while IFS=';' read -r -a BARS; do
        NOW=$(date +%s)
        SOUND=false
        OUTPUT=""

        # Проверка наличия звука
        for L in "${BARS[@]}"; do
            ((L > 2)) && { SOUND=true; LAST_SOUND=$NOW; break; }
        done

        # Определение режима
        if $SOUND; then
            DEFAULT_MODE=false
        elif ((NOW - LAST_SOUND >= SOUND_TIMEOUT)); then
            DEFAULT_MODE=true
        fi

        # Генерация вывода
        if $DEFAULT_MODE; then
            for C in "${COLORS[@]}"; do
                OUTPUT+="%{F$C}┃%{F-}"
            done
        else
            for I in "${!BARS[@]}"; do
                ((BARS[I] > 2)) && OUTPUT+="%{F${COLORS[I]}}┃%{F-}" || OUTPUT+=" "
            done
        fi

        echo "$OUTPUT"
    done
} &

CAVA_PID=$!
wait $CAVA_PID