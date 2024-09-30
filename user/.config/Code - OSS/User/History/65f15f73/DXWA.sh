#!/bin/bash

hidden=/tmp/syshide.lock
modules="$HOME/.config/i3/polybar/Tokio_night/modules"
config="$HOME/.config/stalonetray/stalonetrayrc"

if pgrep -x "stalonetray" > /dev/null
then
    killall stalonetray
    sed -i 's/systray\ninitial=.*/systray\ninitial=2/g' "$modules"
else
    stalonetray --config $config
    sed -i 's/systray\ninitial=.*/systray\ninitial=1/g' "$modules"
fi