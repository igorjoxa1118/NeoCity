#!/usr/bin/bash

#Serash youtube

input=$(yad \
 --title="" \
 --text="Please enter your details:" \
 --image="/usr/share/icons/Tango/scalable/emotes/face-smile.svg" \
 --form \
 --field="Search your track or enter playlist URL " \
 --fixed \
 --width=600 \
 --height=100 \
 --separator="\t")
 
if [[ $input =~ "https" ]]; then
   mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "$input"
else
   mpv ytdl://ytsearch:"$input" --no-video -ao=pulse --term-playing-msg='Title: ${media-title}'
fi