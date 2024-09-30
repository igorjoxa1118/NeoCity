#!/bin/bash

#set -x 

function close_exit() {
   killall yad
}
export -f close_exit
yad \
   --title="Search-tube" \
   --text="What are you want?" \
   --image="./icons/backup.svg" \
   --text-align=center \
   --fixed \
   --width=280 \
   --height=100 \
   --button-align=center \
   --button="Exit:bash -c close_exit" \
   --button="Audio:bash -c mpv_audio" \
   --button="Video:bash -c mpv_video" \
   --separator="\t"