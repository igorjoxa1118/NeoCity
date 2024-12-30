#!/bin/bash

# vars
pid="$(pidof picom)"

# exec
if test "$pid"; then
	kill -9 "$pid"
	notify-send "compositor disabled"
else
	picom -b --config $HOME/.config/i3/config.d/picom.conf &
	disown
	notify-send "compositor enabled"
fi
