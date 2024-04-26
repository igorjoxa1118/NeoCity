#!/bin/bash

bat=$(ls /sys/class/power_supply/)

#sed -i "s/BAT1/${bat}/g" "$HOME"/Загрузки/repository/sources_test/modules
#sed -i "s/ADP0/${bat}/g" "$HOME"/Загрузки/repository/sources_test/modules

echo $bat