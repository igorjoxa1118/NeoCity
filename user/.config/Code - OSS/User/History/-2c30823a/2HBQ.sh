#!/bin/bash

blacklight=$(ls -1 /sys/class/backlight/)

sed -i "s/nvidia_wmi_ec_backlight/${blacklight}/g" "$HOME"/Загрузки/repository/sources_test/modules