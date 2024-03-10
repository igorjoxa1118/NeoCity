#!/bin/bash

hidden=/tmp/syshide.lock
modules="$HOME/.config/i3/polybar/NeoCity/modules"
config="$HOME/.config/stalonetray/stalonetrayrc"

if pgrep -x "stalonetray" > /dev/null
then
    polybar-msg action "#systray.hook.0"
    touch "$hidden"
    killall stalonetray
    sed -i 's/systray\ninitial=.*/systray\ninitial=2/g' "$modules"
else
    polybar-msg action "#systray.hook.1"
    rm "$hidden"
    stalonetray --config $config
    sed -i 's/systray\ninitial=.*/systray\ninitial=1/g' "$modules"
fi