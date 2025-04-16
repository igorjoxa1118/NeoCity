#!/bin/bash

# Получаем данные от nvidia-smi
data=$(nvidia-smi --query-gpu=utilization.gpu,temperature.gpu --format=csv,nounits,noheader)

# Разделяем данные на utilization и temperature
utilization=$(echo "$data" | awk -F ', ' '{print $1}')
temperature=$(echo "$data" | awk -F ', ' '{print $2}')

# Выводим данные в формате, который Polybar может использовать
echo "${utilization}% ${temperature}°C"