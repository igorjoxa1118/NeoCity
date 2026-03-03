#!/bin/bash
# Получаем частоту в кГц и переводим в ГГц
awk '{sum+=$1} END {printf "%.1f", sum/NR/1000000}' /sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq
