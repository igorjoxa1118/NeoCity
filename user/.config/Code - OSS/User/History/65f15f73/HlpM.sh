#!/bin/bash

hidden=/tmp/syshide.lock
file="$HOME/.config/i3/polybar/Tokio_night/modules"

if pgrep -x "stalonetray" > /dev/null
then
    killall stalonetray
    sed -i 's/systray\ninitial=.*/systray\ninitial=2/g' "$file"
else
    stalonetray
    sed -i 's/systray\ninitial=.*/systray\ninitial=1/g' "$file"
fi