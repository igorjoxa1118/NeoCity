#!/bin/bash

blacklight=$(ls -1 /sys/class/backlight/)

sed -i "s/foo/${blacklight}/g" "$HOME"/Загрузки/repository/sources_test/modules