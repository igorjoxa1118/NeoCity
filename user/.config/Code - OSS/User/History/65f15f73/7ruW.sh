#!/bin/bash

file="$HOME/.config/stalonetray/stalonetrayrc"

if pgrep -x "stalonetray" > /dev/null
then
    killall stalonetray
else
    stalonetray
fi