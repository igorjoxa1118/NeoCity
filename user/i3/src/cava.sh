#!/bin/bash

# 1. Проверка, установлена ли утилита cava
if ! command -v cava &> /dev/null; then
    echo "Ошибка: cava не найдена. Пожалуйста, установите ее." >&2
    exit 1
fi

# 2. Атомарная блокировка через создание директории для предотвращения гонки
LOCK_DIR="/tmp/cava.lock"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
    # Если директория уже есть, проверяем, жив ли связанный с ней процесс
    if [ -f "$LOCK_DIR/pid" ] && ps -p "$(cat "$LOCK_DIR/pid")" >/dev/null 2>&1; then
        echo "Другой экземпляр скрипта уже запущен." >&2
        exit 1
    else
        # Процесс мертв, удаляем старую директорию блокировки и создаем новую
        rm -rf "$LOCK_DIR"
        mkdir "$LOCK_DIR"
    fi
fi
# Записываем PID текущего скрипта в файл внутри директории блокировки
echo $$ > "$LOCK_DIR/pid"

# Конфигурационный файл для CAVA
CONFIG_FILE="/tmp/cava_config_$$"
cat >"$CONFIG_FILE" <<'EOF'
[general]
bars = 15
framerate = 60
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

# Цветовая схема (Catppuccin)
COLORS=(
    "#89b4fa" "#f38ba8" "#fab387" "#a6e3a1" "#94e2d5" 
    "#74c7ec" "#cba6f7" "#f5e0dc" "#89b4fa" "#f38ba8"
    "#fab387" "#a6e3a1" "#94e2d5" "#74c7ec" "#cba6f7"
)

# Функция очистки временных файлов при выходе
cleanup() {
    # Завершаем фоновый процесс CAVA
    if [ -n "$CAVA_PID" ]; then
        kill "$CAVA_PID" 2>/dev/null
    fi
    # Удаляем временные файлы и директорию блокировки
    rm -f "$CONFIG_FILE"
    rm -rf "$LOCK_DIR"
    exit 0
}
trap cleanup EXIT TERM INT

# Запуск CAVA и передача его вывода в цикл while
cava -p "$CONFIG_FILE" | {
    LAST_SOUND_TIME=$(date +%s)
    SOUND_TIMEOUT=2
    IN_DEFAULT_MODE=true

    while IFS=';' read -r -a BARS; do
        NOW=$(date +%s)
        IS_SOUND_PRESENT=false
        OUTPUT=""

        # Проверка наличия звука
        for BAR_HEIGHT in "${BARS[@]}"; do
            # 3. Сравнение с помощью [[ -gt ]] для большей надежности
            if [[ "$BAR_HEIGHT" -gt 2 ]]; then
                IS_SOUND_PRESENT=true
                LAST_SOUND_TIME=$NOW
                break
            fi
        done

        # Определение режима отображения
        if $IS_SOUND_PRESENT; then
            IN_DEFAULT_MODE=false
        elif ((NOW - LAST_SOUND_TIME >= SOUND_TIMEOUT)); then
            IN_DEFAULT_MODE=true
        fi

        # Генерация вывода для polybar
        if $IN_DEFAULT_MODE; then
            # Режим по умолчанию: статичные полосы при отсутствии звука
            for COLOR in "${COLORS[@]}"; do
                OUTPUT+="%{F$COLOR}┃%{F-}"
            done
        else
            # Активный режим: анимированные полосы
            for I in "${!BARS[@]}"; do
                if [[ "${BARS[I]}" -gt 2 ]]; then
                    OUTPUT+="%{F${COLORS[I]}}┃%{F-}"
                else
                    OUTPUT+=" "
                fi
            done
        fi
        echo "$OUTPUT"
    done
} &

CAVA_PID=$!
wait $CAVA_PID
