#!/bin/bash



eth_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wlan_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

echo "Мой без-провод: $wlan_int"
echo "Мой провод: $eth_int"