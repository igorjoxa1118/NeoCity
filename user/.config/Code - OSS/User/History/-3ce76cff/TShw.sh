##!/bin/sh

# make sure to kill script and zscroll if mpv exits
while :
     do
       sleep 1
     if ! pidof cmus > /dev/null
        then
            killall zscroll
            exit
     fi
done &

zscroll --length 25 --delay 0.3 \
	--match-text "true" "--before-text ' ' --scroll false" \
	--match-text "false" "--before-text ' ' --scroll true" \

wait