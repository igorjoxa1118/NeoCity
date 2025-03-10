#!/bin/bash

# Путь к временному конфигурационному файлу CAVA
config_file="/tmp/bar_cava_config"

# Создание временного конфигурационного файла для CAVA
cat >"$config_file" <<EOF
[general]
bars = 15  # Количество баров
sensitivity = 250  # Чувствительность

[input]
method = pulse
source = auto

[output]
method = raw
raw_target = /dev/stdout
data_format = ascii
ascii_max_range = 7  # Значение по умолчанию

[color]
gradient = 0  # Отключаем градиент

[smoothing]
integral = 70  # Сглаживание баров

[fft]
mode = high  # Режим FFT
EOF

# Акцентные цвета Catppuccin Mocha
colors=(
    "#89b4fa" "#f38ba8" "#fab387" "#a6e3a1" "#94e2d5"
    "#74c7ec" "#cba6f7" "#f5e0dc" "#89b4fa" "#f38ba8"
    "#fab387" "#a6e3a1" "#94e2d5" "#74c7ec" "#cba6f7"
)

# Запуск CAVA и обработка вывода
cava -p "$config_file" | while IFS=';' read -r -a bars; do
    # Строка для вывода в Polybar
    output=""

    # Проходим по каждому бару
    for ((i = 0; i < ${#bars[@]}; i++)); do
        level=${bars[$i]}
        # Нормализуем уровень до диапазона 0-8 (для символов)
        normalized_level=$(( (level * 8) / 7 ))

        # Выбираем символ в зависимости от нормализованного уровня
        case $normalized_level in
            0) symbol=" ";;
            1) symbol="▁";;
            2) symbol="▂";;
            3) symbol="▃";;
            4) symbol="▄";;
            5) symbol="▅";;
            6) symbol="▆";;
            7) symbol="▇";;
            8) symbol="█";;
            *) symbol=" ";;
        esac

        # Добавляем цветной символ в строку вывода
        output+="%{F${colors[$i]}}$symbol%{F-}"
    done

    # Выводим результат в Polybar
    echo "$output"
done