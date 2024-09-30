#!/bin/bash

set -x

file="$HOME/.config/stalonetray/stalonetrayrc"
hidden=/tmp/syshide.lock
modules="$HOME/.config/i3/polybar/Tokio_night/modules"

if pgrep -x "stalonetray" > /dev/null
then
    killall stalonetray
else
    polybar-msg action "#systray.hook.1"
    xdo hide -n stalonetray
    sed -i 's/systray\ninitial=.*/systray\ninitial=2/g' "$modules"
fi