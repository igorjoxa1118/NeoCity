#!/bin/bash

# Чтение текущей темы
if [ ! -f "$HOME/.config/i3/config.d/.rice" ]; then
    log "Файл .rice не найден!"
    exit 1
fi

read -r RICETHEME < "$HOME/.config/i3/config.d/.rice"

# Пути к директориям с обоями
LIGHT_WALLPAPER_DIR="$HOME/.config/i3/rices/$RICETHEME/walls/light/"
DARK_WALLPAPER_DIR="$HOME/.config/i3/rices/$RICETHEME/walls/dark/"

# Файлы блокировки и конфигурации
LOCK_FILE="$HOME/.config/i3/config.d/.wallpaper_change.lock"
THEME_MODE_FILE="/tmp/.wallpaper_theme_mode"  # Временный файл в /tmp
CONFIG_FILE="$HOME/.wallpaper_time_config"

# Очистка lock-файла при старте (на случай аварийного завершения)
rm -f "$LOCK_FILE"

# Функция для безопасного завершения
cleanup() {
    rm -f "$LOCK_FILE"
    exit
}
trap cleanup EXIT INT TERM

# Проверяем, не выбрал ли пользователь тему в текущей сессии
if [ -f "$THEME_MODE_FILE" ]; then
    exit 0  # Пользователь сделал выбор - не меняем автоматически
fi

# Проверяем lock-файл
if [ -f "$LOCK_FILE" ]; then
    exit 1
fi
touch "$LOCK_FILE"

# Функция случайного выбора обоев
get_random_wallpaper() {
    local dir=$1
    local wallpapers=("$dir"*)
    local count=${#wallpapers[@]}
    
    if [ $count -eq 0 ]; then
        echo "Ошибка: нет обоев в директории $dir" >&2
        exit 1
    fi
    echo "${wallpapers[$((RANDOM % count))]}"
}

# Загружаем настройки времени
load_config() {
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
    else
        DAY_START=6   # 6:00 утра по умолчанию
        DAY_END=18    # 18:00 вечера по умолчанию
    fi
}

# Установка обоев
set_wallpaper() {
    feh --bg-scale "$1"  # Можно заменить на nitrogen при необходимости
}

# Основная логика
load_config
CURRENT_HOUR=$(date +%H)

if [ "$CURRENT_HOUR" -ge "$DAY_START" ] && [ "$CURRENT_HOUR" -lt "$DAY_END" ]; then
    set_wallpaper "$(get_random_wallpaper "$LIGHT_WALLPAPER_DIR")"
else
    set_wallpaper "$(get_random_wallpaper "$DARK_WALLPAPER_DIR")"
fi