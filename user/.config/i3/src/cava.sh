#!/bin/bash

# Путь к временному конфигурационному файлу CAVA
config_file="/tmp/bar_cava_config"

# Создание временного конфигурационного файла для CAVA
cat >"$config_file" <<EOF
[general]
bars = 15  # Количество баров
sensitivity = 150  # Уменьшено для более резкой реакции

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
integral = 150  # Уменьшено для более быстрой реакции
gravity = 150   # Уменьшено для более быстрого опускания баров
fft_filter = 1
frequency_range = 20-1352,1352-2684,2684-4016,4016-5348,5348-6680,6680-8012,8012-9344,9344-10676,10676-12008,12008-13340,13340-14672,14672-16004,16004-17336,17336-18668,18668-20000

[fft]
mode = peak  # Более резкая реакция на изменения звука
EOF

# Акцентные цвета Catppuccin
colors=(
    "#89b4fa" "#f38ba8" "#fab387" "#a6e3a1" "#94e2d5"
    "#74c7ec" "#cba6f7" "#f5e0dc" "#89b4fa" "#f38ba8"
    "#fab387" "#a6e3a1" "#94e2d5" "#74c7ec" "#cba6f7"
)

# Переменные для отслеживания состояния звука
last_sound_time=$(date +%s)
sound_timeout=1  # Таймаут уменьшен до 1 секунды
default_mode=true

# Запуск CAVA и обработка вывода
cava -p "$config_file" | while IFS=';' read -r -a bars; do
    current_time=$(date +%s)
    output=""
    sound_detected=false

    # Проверяем, есть ли звук (хотя бы один бар выше порога)
    for level in "${bars[@]}"; do
        if (( level > 2 )); then
            sound_detected=true
            last_sound_time=$current_time
            break
        fi
    done

    # Определяем режим отображения
    if $sound_detected; then
        default_mode=false
    elif (( current_time - last_sound_time >= sound_timeout )); then
        default_mode=true
    fi

    # Генерируем вывод в зависимости от режима
    if $default_mode; then
        # Режим по умолчанию - все бары видны
        for ((i = 0; i < ${#colors[@]}; i++)); do
            output+="%{F${colors[$i]}}┃%{F-}"
        done
    else
        # Режим с реакцией на звук
        for ((i = 0; i < ${#bars[@]}; i++)); do
            level=${bars[$i]}
            if (( level > 2 )); then
                output+="%{F${colors[$i]}}┃%{F-}"
            else
                output+=" "
            fi
        done
    fi

    # Выводим результат в Polybar
    echo "$output"
done