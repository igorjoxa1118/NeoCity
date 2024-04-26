#!/bin/bash

ad=$(ls /sys/class/power_supply/ | awk 'NR==1 { print $2 }')
bat=$(ls /sys/class/power_supply/ | awk 'NR==2 { print $2 }')
#sed -i "s/BAT1/${bat}/g" "$HOME"/Загрузки/repository/sources_test/modules
#sed -i "s/ADP0/${ad}/g" "$HOME"/Загрузки/repository/sources_test/modules

echo $ad
echo $bat 