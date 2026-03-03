#!/bin/sh

# Чтение текущей темы
if [ ! -f "$HOME/.config/i3/config.d/.rice" ]; then
    log "Файл .rice не найден!"
    exit 1
fi

read -r RICETHEME < "$HOME/.config/i3/config.d/.rice"

# Завершаем Polybar
polybar-msg cmd quit

# Запускаем основную панель
polybar -c ~/.config/i3/rices/$RICETHEME/config.ini main &

# Запускаем вторую панель
polybar -c ~/.config/i3/rices/$RICETHEME/config.ini secondary &

# Запускаем вторую панель
polybar -c ~/.config/i3/rices/$RICETHEME/config.ini right &

# Уведомляем пользователя
notify-send "Polybar" "Перезагрузка Polybar и темы"