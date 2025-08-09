#!/usr/bin/env bash
set -euo pipefail

# --- Проверка наличия cava
if ! command -v cava &>/dev/null; then
    echo "Ошибка: утилита cava не найдена. Установите её." >&2
    exit 1
fi

# --- Файловая блокировка через flock
LOCK_FILE="/tmp/cava.lock"
exec 200>"$LOCK_FILE"
flock -n 200 || {
    echo "Ошибка: другой экземпляр уже запущен." >&2
    exit 1
}

# --- Генерация временного конфига
CONFIG_FILE="$(mktemp /tmp/cava_config.XXXXXX)"
cat >"$CONFIG_FILE" << 'EOF'
[general]
bars = 16
channels = stereo
framerate = 60
# Уменьшаем чувствительность для еще более широкого динамического диапазона
sensitivity = 50

[input]
method = pulse
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 5

[color]
gradient = 0

[smoothing]
# Уменьшены значения сглаживания для более резкой и "прыгающей" реакции
integral = 40
gravity = 40
EOF

# --- Параметры звука
SOUND_THRESHOLD=0
SOUND_TIMEOUT=2
LAST_SOUND_TIME=$(date +%s)

# --- Параметры смены цвета
COLOR_CHANGE_INTERVAL=3  # секунд между обновлениями цвета
LAST_COLOR_UPDATE=$(date +%s)

# --- Цвет режима простоя
IDLE_COLOR="#2C3A51"

# --- Градиентная палитра Catppuccin Mocha
SATURATED_COLORS=(
    "#f5e0dc"  # rosewater
    "#f2cdcd"  # flamingo
    "#f5c2e7"  # pink
    "#e6e9c9"  # mauve
    "#a6e3a1"  # green
    "#94e2d5"  # teal
    "#89dceb"  # sky
    "#74c7ec"  # sapphire
    "#89b4fa"  # blue
    "#cba6f7"  # lavender
)
NUM_BARS=16 # Увеличено до 16 для стерео

# --- Инициализация текущих цветов для каждого бара
CURRENT_COLORS=()
for ((i=0; i<NUM_BARS; i++)); do
    CURRENT_COLORS[i]="${SATURATED_COLORS[RANDOM % ${#SATURATED_COLORS[@]}]}"
done

# --- Очистка при выходе
cleanup() {
    kill "${CAVA_PID:-}" 2>/dev/null || true
    rm -f "$CONFIG_FILE"
}
trap cleanup EXIT TERM INT

# --- Запуск cava и цикл обработки вывода
cava -p "$CONFIG_FILE" | while IFS=';' read -r -a BARS; do
    NOW=$(date +%s)
    OUTPUT=""

    # проверка звука и определение режима
    SOUND=false
    for h in "${BARS[@]}"; do
        if (( h > SOUND_THRESHOLD )); then
            SOUND=true
            LAST_SOUND_TIME=$NOW
            break
        fi
    done

    # обновление цветов всех баров одновременно по интервалу
    if (( NOW - LAST_COLOR_UPDATE >= COLOR_CHANGE_INTERVAL )); then
        for ((i=0; i<NUM_BARS; i++)); do
            CURRENT_COLORS[i]="${SATURATED_COLORS[RANDOM % ${#SATURATED_COLORS[@]}]}"
        done
        LAST_COLOR_UPDATE=$NOW
    fi

    # если звук есть в последние SOUND_TIMEOUT сек, активный режим
    if (( NOW - LAST_SOUND_TIME < SOUND_TIMEOUT )); then
        # Левый канал (первая половина баров)
        for ((i=0; i<NUM_BARS/2; i++)); do
            if (( BARS[i] > SOUND_THRESHOLD )); then
                OUTPUT+="%{F${CURRENT_COLORS[i]}}┃%{F-}"
            else
                OUTPUT+="%{F${IDLE_COLOR}}┃%{F-}"
            fi
        done

        # Правый канал (вторая половина баров)
        for ((i=NUM_BARS/2; i<NUM_BARS; i++)); do
            if (( BARS[i] > SOUND_THRESHOLD )); then
                OUTPUT+="%{F${CURRENT_COLORS[i]}}┃%{F-}"
            else
                OUTPUT+="%{F${IDLE_COLOR}}┃%{F-}"
            fi
        done
    else
        # idle: все столбики идут в IDLE_COLOR и не исчезают
        for _ in "${BARS[@]}"; do
            OUTPUT+="%{F${IDLE_COLOR}}┃%{F-}"
        done
    fi

    echo "$OUTPUT"
done &

CAVA_PID=$!
wait "$CAVA_PID"