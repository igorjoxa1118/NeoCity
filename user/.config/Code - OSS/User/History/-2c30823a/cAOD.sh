#!/bin/bash

en_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wl_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

if [ ! -z "$eth_int" ]; then
echo "Мой провод: $eth_int"
elif  
echo "Какой провод?"
fi

if [ ! -z "$wlan_int" ]; then
echo "Мой без-провод: $wlan_int"
else
echo "Какой без-провод?"
fi


