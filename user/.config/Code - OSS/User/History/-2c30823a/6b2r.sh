#!/bin/bash

bat=$(ls /sys/class/power_supply/ | awk -F: '{ print $2;getline }')
ad=$(ls /sys/class/power_supply/ | awk -F: '{ print $2;getline }')
#sed -i "s/BAT1/${bat}/g" "$HOME"/Загрузки/repository/sources_test/modules
#sed -i "s/ADP0/${ad}/g" "$HOME"/Загрузки/repository/sources_test/modules

echo $bat 
echo $ad