#!/bin/bash

file="$HOME/.config/stalonetray/stalonetrayrc"
hidden=/tmp/syshide.lock

if pgrep -x "stalonetray" > /dev/null
then
    killall stalonetray
else
    polybar-msg action "#systray.hook.1"
    xdo hide -n stalonetray
    touch "$hidden"
    sed -i 's/systray\ninitial=.*/systray\ninitial=2/g' "$file"
fi