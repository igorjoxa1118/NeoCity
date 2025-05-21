#!/usr/bin/env bash

# ===== НАСТРОЙКИ =====
MAX_LEN=40           # Максимальная длина отображаемого текста
SCROLL_LEN=25        # Длина видимой области при скроллинге
DELAY=0.3            # Скорость скроллинга (меньше = быстрее)
PADDING="   "        # Буферные пробелы для плавного скролла

# Цвета (значения по умолчанию Catppuccin Mocha)
COLOR_PLAYING="#a6e3a1"   # Зеленый
COLOR_PAUSED="#f9e2af"    # Желтый
COLOR_STOPPED="#f38ba8"   # Красный
COLOR_OFFLINE="#bac2de"   # Серый
COLOR_TEXT="#cdd6f4"      # Основной текст
COLOR_ICON="#b4befe"      # Цвет иконки

# Иконки (Nerd Font)
ICON_PLAYING=""
ICON_PAUSED=""
ICON_STOPPED=""
ICON_OFFLINE=""

# ===== ФУНКЦИИ =====
format_output() {
    local icon="$1"
    local status_color="$2"
    local text="$3"
    echo "%{F$status_color}$icon%{F-} %{F$COLOR_TEXT}$text%{F-}"
}

# ===== ГЛАВНЫЙ ЦИКЛ =====
while true; do
    # Получаем текущий трек и статус
    track=$(mpc --format "%artist% - %title%" current 2>/dev/null || echo "MPD offline")
    status=$(mpc status 2>/dev/null | grep -oP '\[playing\]|\[paused\]|\[stopped\]' || echo "offline")

    # Определяем цвет и иконку по статусу
    case "$status" in
        "[playing]") 
            icon="$ICON_PLAYING"
            status_color="$COLOR_PLAYING"
            ;;
        "[paused]")  
            icon="$ICON_PAUSED"
            status_color="$COLOR_PAUSED"
            ;;
        "[stopped]") 
            icon="$ICON_STOPPED"
            status_color="$COLOR_STOPPED"
            ;;
        *)           
            icon="$ICON_OFFLINE"
            status_color="$COLOR_OFFLINE"
            ;;
    esac

    # Если трек пустой или MPD не доступен
    if [ -z "$track" ] || [ "$track" = "MPD offline" ]; then
        format_output "$icon" "$status_color" "$track"
        sleep 1
        continue
    fi
    
    # Подготавливаем текст для скроллинга
    text="${PADDING}${track}${PADDING}"
    text_len=${#text}
    
    # Если трек короче SCROLL_LEN, показываем без скролла
    if [ ${#track} -le $SCROLL_LEN ]; then
        format_output "$icon" "$status_color" "$track"
        sleep 1
        continue
    fi
    
    # Цикл скроллинга с проверкой изменений
    while true; do
        # Проверяем изменения
        new_track=$(mpc --format "%artist% - %title%" current 2>/dev/null)
        new_status=$(mpc status 2>/dev/null | grep -oP '\[playing\]|\[paused\]|\[stopped\]' || echo "offline")
        
        if [ "$new_track" != "$track" ] || [ "$new_status" != "$status" ]; then
            break
        fi
        
        # Скролл влево
        for ((i=0; i<=text_len-SCROLL_LEN; i++)); do
            format_output "$icon" "$status_color" "${text:i:SCROLL_LEN}"
            sleep $DELAY
        done
        
        # Скролл вправо
        for ((i=text_len-SCROLL_LEN; i>=0; i--)); do
            format_output "$icon" "$status_color" "${text:i:SCROLL_LEN}"
            sleep $DELAY
        done
        
        sleep 0.5  # Пауза между циклами
    done
done