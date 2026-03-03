#!/bin/bash

# Завершаем старые процессы
pkill xwinwrap
pkill pcmanfm

# Немного подождать, чтобы всё очистилось
sleep 0.5

# Запустить рабочий стол через xwinwrap
xwinwrap -ov -g 1920x1080+0+0 -- \
    pcmanfm --desktop
