#!/bin/bash

en_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
et_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wl_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

if [ ! -z "$en_int" ]; then
echo "Мой провод: $en_int"
else
echo "Мой провод: $et_int"
fi

if [ ! -z "$wl_int" ]; then
echo "Мой без-провод: $wl_int"
else
echo "Какой без-провод?"
fi


