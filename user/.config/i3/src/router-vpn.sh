#!/bin/bash

# Настройки SSH
SSH_USER="root"
ROUTER_IP="192.168.1.7"
SSH_PORT="1311"
SSH_KEY_PATH="/home/vir0id/.ssh/waybar_ed25519"

# Команда для проверки наличия интерфейса 'tun0'
CHECK_COMMAND="ifconfig tun0"

# Выполняем команду на роутере через SSH, используя ключ без пароля
if ssh -o BatchMode=yes -i "$SSH_KEY_PATH" -p "$SSH_PORT" "$SSH_USER@$ROUTER_IP" "$CHECK_COMMAND" > /dev/null 2>&1; then
    # Если команда успешна, выводим текст для Polybar
    echo "ON"
    exit 0
else
    # Если команда не успешна, выводим текст для Polybar
    echo "OFF"
    exit 1
fi