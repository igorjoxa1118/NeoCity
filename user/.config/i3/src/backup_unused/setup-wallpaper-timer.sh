#!/usr/bin/env bash

# =============================================
# Автоматическая настройка смены обоев через systemd
# с проверкой зависимостей и безопасной перезагрузкой
# =============================================

# --- Конфигурация ---
REAL_USER="${SUDO_USER:-$USER}"                    # Определяем реального пользователя
HOME_DIR=$(getent passwd "$REAL_USER" | cut -d: -f6) # Корректный домашний каталог
SERVICE_NAME="wallpaper-changer"                   # Имя сервиса (без .service)

# --- Пути ---
SERVICE_FILE="$HOME_DIR/.config/systemd/user/$SERVICE_NAME.service"
TIMER_FILE="$HOME_DIR/.config/systemd/user/$SERVICE_NAME.timer"
SCRIPT_PATH="$HOME_DIR/.config/i3/src/set_first_start_wallpaper.sh"
LOG_FILE="/tmp/$SERVICE_NAME-install.log"

# --- Проверки ---

# Запрет запуска от root
if [ "$(id -u)" -eq 0 ]; then
    echo -e "\033[1;31mОШИБКА:\033[0m Не запускайте скрипт с sudo!" >&2
    echo "  Правильно: $0" >&2
    exit 1
fi

# Проверка существования скрипта обоев
if [ ! -f "$SCRIPT_PATH" ]; then
    echo -e "\033[1;31mОШИБКА:\033[0m Скрипт обоев не найден:" >&2
    echo "  $SCRIPT_PATH" >&2
    exit 1
fi

# Проверка зависимостей
if ! command -v systemctl >/dev/null; then
    echo -e "\033[1;31mТРЕБУЕТСЯ:\033[0m systemd не установлен" >&2
    exit 1
fi

# --- Создание файлов systemd ---

mkdir -p "$HOME_DIR/.config/systemd/user"

# Сервисный файл
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Automatic wallpaper changer for $REAL_USER

[Service]
Type=simple
ExecStart=$SCRIPT_PATH
Environment="DISPLAY=:0"
Environment="DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%U/bus"
StandardOutput=file:/tmp/$SERVICE_NAME.log
StandardError=inherit
Restart=on-failure

[Install]
WantedBy=default.target
EOF

# Таймер
cat > "$TIMER_FILE" <<EOF
[Unit]
Description=Run wallpaper changer every minute for $REAL_USER

[Timer]
OnBootSec=1min
OnUnitActiveSec=1min
AccuracySec=1s

[Install]
WantedBy=timers.target
EOF

# --- Активация сервиса ---
systemctl --user daemon-reload
systemctl --user enable --now "$SERVICE_NAME.timer"

# --- Проверка установки ---
echo -e "\n\033[1;32mУСПЕШНО:\033[0m Сервис настроен для пользователя \033[1;33m$REAL_USER\033[0m"
echo -e "▪ Сервис: \033[1;34m$SERVICE_FILE\033[0m"
echo -e "▪ Таймер: \033[1;34m$TIMER_FILE\033[0m"
echo -e "▪ Скрипт: \033[1;34m$SCRIPT_PATH\033[0m"

# --- Интерактивная перезагрузка ---
echo -e "\n\033[1;36mДЛЯ ЗАВЕРШЕНИЯ:\033[0m"
echo -e "1. Изменения применятся после перезагрузки или команды:"
echo -e "   \033[1;37msystemctl --user daemon-reload\033[0m"

read -p "2. Перезагрузить компьютер сейчас? [y/N] " answer
if [[ "$answer" =~ ^[YyДд]$ ]]; then
    echo -e "\n\033[1;33mПерезагрузка через 15 секунд...\033[0m"
    echo -e "Для отмены нажмите \033[1;31mCtrl+C\033[0m"
    sleep 15
    sudo -k shutdown -r now  # -k сбрасывает кеш паролей sudo
else
    echo -e "\n\033[1;32mГОТОВО!\033[0m Ручная перезагрузка не требуется."
    echo -e "Таймер уже активен. Проверить статус:"
    echo -e "  \033[1;37msystemctl --user list-timers\033[0m\n"
fi