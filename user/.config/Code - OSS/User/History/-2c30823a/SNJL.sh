#!/bin/bash



eth_int=$(ip link | awk -F: '$0 !~ "lo|vir|wl|^[^0-9]"{print $2;getline}')
wlan_int=$(ip link | awk -F: '{ print $2;getline }' | grep w)

echo "Мой без-провод: "$wlan_int"
echo "Мой провод: "$eth_int"