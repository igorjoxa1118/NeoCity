#!/bin/bash
#set -x

work_dir=$(pwd)

# Запрос порта SSH у пользователя
read -p "Введите порт для SSH (по умолчанию 22): " ssh_port
ssh_port=${ssh_port:-22}  # Если порт не указан, используем 22

# Определение подсети (например, 192.168.1)
read -p "Введите подсеть (например, 192.168.1): " subnet

# Функция для проверки наличия открытого порта
check_port() {
    nc -z -w 1 $1 $2 && echo "$1:$2 is open"
}

# Массив для хранения доступных IP-адресов
available_ips=()

# Проверка доступных IP-адресов
echo "Проверка доступных IP-адресов в подсети $subnet..."
for i in {1..11}; do
    ip="$subnet.$i"
    if check_port $ip $ssh_port; then
        echo "SSH доступен на $ip"
        available_ips+=($ip)
    fi
done

# Предложение подключения к доступным адресам
if [ ${#available_ips[@]} -eq 0 ]; then
    echo "Нет доступных IP-адресов."
    exit 1
fi

# Сохранение доступных IP-адресов для последующего подключения
if [ ${#available_hosts[@]} -eq 0 ]; then
    echo "Нет доступных SSH-хостов."
else
    echo "Доступные SSH-хосты: ${available_hosts[@]}"
    
    # Запись доступных адресов в файл (или другую ячейку памяти)
    #echo "${available_hosts[@]}" > $work_dir/available_hosts.txt 
    #echo "Доступные адреса сохранены в $work_dir/available_hosts.txt" 
fi

echo "Доступные IP-адреса для подключения по SSH:"
select ip in "${available_ips[@]}"; do
    if [[ -n "$ip" ]]; then
        echo "Подключение к $ip по SSH на порту $ssh_port..."
        # Имя пользователя
        read -p "Введите имя пользователя SSH: " ssh_name
        ssh -p "$ssh_port" "$ssh_name@$ip"
        break
    else
        echo "Недопустимый выбор. Попробуйте снова."
    fi
done