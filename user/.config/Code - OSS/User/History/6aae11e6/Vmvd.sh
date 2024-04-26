#!/bin/bash

#set -x 
user="$(pwd)"

function close_exit() {
   killall yad
}
export -f close_exit

function menu () {
     kitty -e $user/.bin/BackUpMenu/bin/1-Install_part_in_fstab.sh
}
export -f menu

function usb() {
     kitty -e $user/./bin/BackUpMenu/bin/2-Backup_skel_to_USB.sh
} 
export -f usb

yad \
   --title="Search-tube" \
   --text="What are you want?" \
   --image="./icons/backup.svg" \
   --text-align=center \
   --fixed \
   --width=280 \
   --height=100 \
   --fore="#bb9af7" \
   --back="#16161E" \
   --button-align=center \
   --button="Exit:bash -c close_exit" \
   --button="Modify fstab:bash -c menu" \
   --button="Backup in USB:bash -c usb" \
   --separator="\t"