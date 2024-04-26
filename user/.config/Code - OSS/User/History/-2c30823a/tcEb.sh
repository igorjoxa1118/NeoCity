#!/bin/bash

en_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
et_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wl_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

if [ ! -z "$en_int" ]; then
sed -i "s/provod/${en_int}/g" "$HOME"/Загрузки/repository/sources_test/dot_insall/modules
else
  if [ ! -z "$et_int" ]; then
  sed -i "s/provod/${et_int}/g" "$HOME"/Загрузки/repository/sources_test/dot_insall/modules
  fi
fi

if [ ! -z "$wl_int" ]; then
sed -i "s/b_provod/${wl_int}/g" "$HOME"/Загрузки/repository/sources_test/dot_insall/modules
else
read -p "What is you Wireless connection interface?(Example: wlan0, wlp0s20f3): " wl_int_custom
sed -i "s/b_provod/${wl_int_custom}/g" "$HOME"/Загрузки/repository/sources_test/dot_insall/modules
fi