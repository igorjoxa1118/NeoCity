#!/bin/bash


# vars
# pid="$(pidof dunst)"
pid="$(ps aux | grep dunstrc | grep -v grep | awk -n '{print $2}')"
pid2="$(ps aux | grep musnify-mpd | grep -v grep | awk -n '{print $2}')"

function closed {
	killall dunst
	killall musnify-mpd
}

function start { 
	dunst -conf $HOME/.config/dunst/dunstrc &
	musnify-mpd &
}

# exec
if test "$pid"; then
	if test "$pid2"; then
		kill -9 "$pid2"
	fi
	# killall "dunst"
	kill -9 "$pid"
	closed
fi

start