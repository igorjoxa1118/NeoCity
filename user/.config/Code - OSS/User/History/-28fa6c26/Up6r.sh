#!/bin/bash

#set -x 

function close_exit() {
   killall yad
}
export -f close_exit

function menu () {
     ./bin/1-Install_part_in_fstab.sh
}
export -f menu

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
   --button="Modify fstab:bash -c menu" \
   --button="Backup in USB:bash -c mpv_video" \
   --separator="\t"