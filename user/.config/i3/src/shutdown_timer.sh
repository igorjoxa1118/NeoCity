#!/bin/bash

# 1. Получаем данные из системы
DATA=$(busctl get-property org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager ScheduledShutdown | grep -oE '[0-9]+' | head -n 1)

# 2. Если таймер НЕ запущен (пусто или 0)
if [[ -z "$DATA" || "$DATA" == "0" ]]; then
    echo " 00:00"  # Текст по умолчанию
    exit 0
fi

# 3. Если таймер запущен — считаем время
TARGET_SEC=$((DATA / 1000000))
NOW_SEC=$(date -u +%s)
DIFF=$((TARGET_SEC - NOW_SEC))

# Если время почему-то в минусе
if [ $DIFF -le 0 ]; then
    echo " 00:00"
    exit 0
fi

# 4. Расчет часов и минут
HOURS=$((DIFF / 3600))
MINS=$(( (DIFF % 3600) / 60 ))

if [ $HOURS -gt 0 ]; then
    echo " ${HOURS}ч ${MINS}м"
else
    [[ $MINS -eq 0 ]] && MINS=1
    echo " ${MINS} мин"
fi