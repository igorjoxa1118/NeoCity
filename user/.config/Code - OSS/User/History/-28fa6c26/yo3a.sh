#!/bin/bash

#set -x 

yad \
   --title="Search-tube" \
   --text="What are you want?" \
   --image="./icons/backup.svg" \
   --text-align=center \
   --fixed \
   --width=280 \
   --height=100 \
   --button-align=center \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/window-close.svg!Exit:bash -c close_exit_sec" \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/go-down-skip.svg!Close:bash -c close" \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/audio-volume-medium.svg!Audio:bash -c mpv_audio" \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/filmgrain.svg!Video:bash -c mpv_video" \
   --separator="\t"