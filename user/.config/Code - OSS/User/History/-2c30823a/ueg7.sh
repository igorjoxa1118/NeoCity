#!/bin/bash



read -p "What is you Wireless network interface?: " wlan_int

sed -i "s/wlp0s20f3/${wlan_int}/g" "$HOME"/Загрузки/repository/sources_test/modules