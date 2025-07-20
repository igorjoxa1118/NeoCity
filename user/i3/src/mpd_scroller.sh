#!/usr/bin/env bash

# ===== НАСТРОЙКИ =====
MAX_LEN=40           # Максимальная длина отображаемого текста
SCROLL_LEN=25        # Длина видимой области при скроллинге
DELAY=0.3            # Скорость скроллинга (меньше = быстрее)
PADDING="   "        # Буферные пробелы для плавного скролла

# Цвета (Catppuccin catppuccin-mocha)
COLOR_PLAYING="#a6e3a1"   # Зеленый
COLOR_PAUSED="#f38ba8"    # Желтый
COLOR_STOPPED="#f9e2af"   # Красный
COLOR_OFFLINE="#bac2de"   # Серый
COLOR_TEXT="#cdd6f4"      # Основной текст
# ===== ФУНКЦИИ =====
format_output() {
    local status_color="$1"
    local text="$2"
    echo "%{F$status_color}$text%{F-}"
}

safe_mpc() {
    mpc --format "%artist% - %title%" current 2>/dev/null || echo "MPD offline"
}

get_status() {
    mpc status 2>/dev/null | grep -oP '\[playing\]|\[paused\]|\[stopped\]' || echo "offline"
}

# ===== ГЛАВНЫЙ ЦИКЛ =====
while true; do
    # Получаем текущий трек и статус с обработкой ошибок
    track=$(safe_mpc)
    status=$(get_status)

    # Определяем цвет по статусу
    case "$status" in
        "[playing]") status_color="$COLOR_PLAYING" ;;
        "[paused]")  status_color="$COLOR_PAUSED" ;;
        "[stopped]") status_color="$COLOR_STOPPED" ;;
        *)           status_color="$COLOR_OFFLINE" ;;
    esac

    # Если трек пустой или MPD не доступен
    if [ -z "$track" ] || [ "$track" = "MPD offline" ]; then
        format_output "$status_color" "$track"
        sleep 1
        continue
    fi
    
    # Подготавливаем текст для скроллинга
    text="${PADDING}${track}${PADDING}"
    text_len=${#text}
    
    # Если трек короче SCROLL_LEN, показываем без скролла
    if [ ${#track} -le $SCROLL_LEN ]; then
        format_output "$status_color" "$track"
        sleep 1
        continue
    fi
    
    # Цикл скроллинга с проверкой изменений
    while true; do
        # Проверяем изменения с обработкой ошибок
        new_track=$(safe_mpc)
        new_status=$(get_status)
        
        if [ "$new_track" != "$track" ] || [ "$new_status" != "$status" ]; then
            break
        fi
        
        # Скролл влево
        for ((i=0; i<=text_len-SCROLL_LEN; i++)); do
            format_output "$status_color" "${text:i:SCROLL_LEN}"
            sleep $DELAY
        done
        
        # Скролл вправо
        for ((i=text_len-SCROLL_LEN; i>=0; i--)); do
            format_output "$status_color" "${text:i:SCROLL_LEN}"
            sleep $DELAY
        done
        
        sleep 0.5  # Пауза между циклами
    done
done