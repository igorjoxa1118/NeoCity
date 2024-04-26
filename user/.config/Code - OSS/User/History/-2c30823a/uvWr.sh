#!/bin/bash

ad=$(ls /sys/class/power_supply/ | awk "NR==1 { print $2 }" | grep A)
bat=$(ls /sys/class/power_supply/ | awk "NR==2 { print $2 }" | grep B)

sed -i "s/ADP0/${ad}/g" "$HOME"/Загрузки/repository/sources_test/modules
sed -i "s/BAT1/${bat}/g" "$HOME"/Загрузки/repository/sources_test/modules
