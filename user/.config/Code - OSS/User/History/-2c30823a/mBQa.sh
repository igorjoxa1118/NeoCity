#!/bin/bash



wlan_int=$(ip -br l | awk '$1 !~ "lo|vir|wl" { print $1}')
eth_int=$(ip link | awk -F: '{ print $2;getline }' | grep w)

echo "Мой провод: $wlan_int"
echo "Мой без-провод: $eth_int"