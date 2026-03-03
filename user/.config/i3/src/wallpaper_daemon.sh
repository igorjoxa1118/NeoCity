#!/usr/bin/env bash

# --- КОНФИГУРАЦИЯ ---
WALL_BASE="$HOME/.config/i3/src/music_walls"
RICETHEME=$(cat "$HOME/.config/i3/config.d/.rice" 2>/dev/null || echo "default")
LIGHT_DIR="$HOME/.config/i3/rices/$RICETHEME/walls/light/"
DARK_DIR="$HOME/.config/i3/rices/$RICETHEME/walls/dark/"
THEME_MODE_FILE="/tmp/.wallpaper_theme_mode"
FIFO="/tmp/wallpaper_events.fifo"
LOCK_FILE="/tmp/wallpaper_update.lock"

# Создаем канал событий
[ -e "$FIFO" ] && rm "$FIFO"
mkfifo "$FIFO"

# Функция подбора картинки (с защитой от пустых папок)
get_wallpaper() {
    local dir="$1"
    local res=$(find "$dir" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.png" \) 2>/dev/null | shuf -n1)
    [ -z "$res" ] && res=$(find "$WALL_BASE" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.png" \) 2>/dev/null | shuf -n1)
    echo "$res"
}

# ГЛАВНАЯ ЛОГИКА (с защитой от параллельного выполнения)
update_wallpaper() {
    # Проверка блокировки ручной темы
    [ -f "$THEME_MODE_FILE" ] && return
    
    # Проверка на параллельное выполнение (через lock file)
    if [ -f "$LOCK_FILE" ]; then
        # Если обновление уже запущено менее 0.5 секунд назад - пропускаем
        local lock_age=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || echo 0)))
        [ "$lock_age" -lt 1 ] && return
    fi
    
    # Создаем lock file
    touch "$LOCK_FILE"
    
    # Ищем реально играющий плеер
    local player=$(playerctl -l 2>/dev/null | while read -r p; do
        [ "$(playerctl -p "$p" status 2>/dev/null)" = "Playing" ] && echo "$p" && break
    done)

    if [ -n "$player" ]; then
        local meta=$(playerctl -p "$player" metadata --format "{{title}} {{artist}}" 2>/dev/null | tr '[:upper:]' '[:lower:]')
        local genre=""

        # Детекция жанра
        [[ "$meta" =~ (metal) ]] && genre="metal"
        [[ "$meta" =~ (rock|punk) ]] && genre="rock"
        [[ "$meta" =~ (chill|lofi|ambient) ]] && genre="chill"
        [[ "$meta" =~ (cyberpunk) ]] && genre="cyberpunk"
        [[ "$meta" =~ (dnb|drum) ]] && genre="dnb"
        [[ "$meta" =~ (synth|retro) ]] && genre="synthwave"

        if [ -z "$genre" ] && [[ "$player" == *"mpd"* || "$meta" =~ (mix|ost|playlist|album) ]]; then
            genre="others"
        fi

        if [ -n "$genre" ]; then
            feh --bg-fill "$(get_wallpaper "$WALL_BASE/$genre")"
            # Удаляем lock file после успешного выполнения
            rm -f "$LOCK_FILE"
            return
        fi
    fi

    # Если музыка на паузе или нет метаданных — день/ночь
    local hour=$(date +%H)
    if (( hour >= 7 && hour < 19 )); then
        feh --bg-fill "$(get_wallpaper "$LIGHT_DIR")"
    else
        feh --bg-fill "$(get_wallpaper "$DARK_DIR")"
    fi
    
    # Удаляем lock file
    rm -f "$LOCK_FILE"
}

# --- УЛУЧШЕННЫЙ ОБРАБОТЧИК СОБЫТИЙ С DEBOUNCE ---
event_handler() {
    local last_update=0
    local debounce_delay=0.8  # секунды
    
    while true; do
        # Ждем событие
        read -r line < "$FIFO"
        
        local current_time=$(date +%s.%N)
        local time_since_last_update=$(echo "$current_time - $last_update" | bc)
        
        # Если с последнего обновления прошло больше debounce_delay секунд
        if (( $(echo "$time_since_last_update > $debounce_delay" | bc -l) )); then
            # Проверяем, есть ли еще события в буфере (неблокирующее чтение)
            local has_more_events=false
            while read -r -t 0.1 _; do
                has_more_events=true
                # Читаем все оставшиеся события (очищаем буфер)
                timeout 0.5 cat "$FIFO" > /dev/null 2>&1 || break
            done < "$FIFO"
            
            # Если были дополнительные события, ждем еще немного
            if [ "$has_more_events" = true ]; then
                sleep 0.3
                # Очищаем возможные новые события
                timeout 0.2 cat "$FIFO" > /dev/null 2>&1
            fi
            
            update_wallpaper
            last_update=$(date +%s.%N)
        else
            # Игнорируем событие, но обновляем время последнего события
            last_update=$(date +%s.%N)
        fi
    done
}

# --- ОЧИСТКА ПРИ ЗАВЕРШЕНИИ ---
cleanup() {
    rm -f "$FIFO" "$LOCK_FILE"
    kill $(jobs -p) 2>/dev/null
    exit 0
}

trap cleanup EXIT INT TERM

# --- ИСТОЧНИКИ СОБЫТИЙ (ОПТИМИЗИРОВАННЫЕ) ---
# 1. Слушаем плеер с фильтрацией (только изменения статуса/трека)
(
    playerctl --follow metadata --format "{{status}} {{artist}} {{title}}" 2>/dev/null | \
    while read -r line; do
        # Игнорируем пустые строки и частые обновления прогресса
        [ -n "$line" ] && echo "player" > "$FIFO"
    done
) &

# 2. Таймер (раз в 10 минут) с проверкой изменений
(
    last_state=""
    while true; do
        sleep 600
        
        # Проверяем текущее состояние
        current_player=$(playerctl -l 2>/dev/null | head -1)
        current_status=$(playerctl -p "$current_player" status 2>/dev/null 2>/dev/null || echo "None")
        current_state="${current_player}:${current_status}"
        
        # Отправляем событие только если состояние изменилось
        [ "$current_state" != "$last_state" ] && echo "timer" > "$FIFO"
        last_state="$current_state"
    done
) &

# 3. Мониторинг ручного выбора темы (дополнительный источник)
(
    inotifywait -m -e create,delete --format "%e" /tmp 2>/dev/null | \
    while read -r event; do
        [[ "$event" =~ "\.wallpaper_theme_mode" ]] && echo "theme_change" > "$FIFO"
    done
) &

# Запуск обработчика
event_handler