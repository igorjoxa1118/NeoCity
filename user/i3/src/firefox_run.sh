#!/bin/bash

# Лог-файл для вывода
LOG_FILE="$HOME/.config/i3/logs/firefox_setup.log"

# Функция для выполнения скрипта в фоновом режиме
run_in_background() {
    UFILE="$HOME/.config/i3/config.d/.fire"

    # Проверяем файл .fire. Если он существует, значит скрипт не выполняется
    if [[ -f "$UFILE" ]]; then
        echo "Configuration already done. Exiting..." >> "$LOG_FILE"
        exit 0
    fi

    # Проверяем, установлен ли Firefox
    if ! command -v firefox &> /dev/null; then
        echo "Firefox не установлен. Устанавливаем..." >> "$LOG_FILE"
        sudo pacman -Sy --noconfirm firefox >> "$LOG_FILE" 2>&1
        if ! command -v firefox &> /dev/null; then
            echo "Не удалось установить Firefox. Выход..." >> "$LOG_FILE"
            exit 1
        fi
        echo "Firefox успешно установлен." >> "$LOG_FILE"
    fi

    # Путь к директории профиля Firefox
    PROFILE_DIR="$HOME/.mozilla/firefox/"

    # Запуск Firefox в фоновом режиме
    firefox > /dev/null 2>&1 &
    FF_PID=$!

    # Ожидание создания файлов настроек
    while [ ! -f "$PROFILE_DIR"/*.default-release/prefs.js ]; do
        sleep 1
    done

    # Закрытие Firefox
    kill $FF_PID

    echo "Firefox завершен после создания файлов настроек." >> "$LOG_FILE"

    # Создаём файл .fire
    touch "$UFILE"
    echo "Configuration completed. Created $UFILE to prevent future runs." >> "$LOG_FILE"
}

# Запуск функции в фоновом режиме
run_in_background &