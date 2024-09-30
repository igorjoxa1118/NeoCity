#!/bin/bash

file="$HOME/.config/stalonetray/stalonetrayrc"

if pgrep -x "stalonetray -c $file" > /dev/null
then
    killall stalonetray
else
    stalonetray
fi