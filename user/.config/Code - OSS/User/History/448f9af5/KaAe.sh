#!/bin/bash

#set -x 

MENUDRIVE() {
BACKTITLE="v.1.0"
MENU="Выберене нужный пункт:"
HEIGHT=30
WIDTH=60
CHOICE_HEIGHT=20

OPTIONS=(1 "Установить разделы в fstab"
         2 "Создать бэкап в USB")

CHOICE=$(yad \
 --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
 --geometry=20x40+500+400 \
 --fontname="Iosevka Term Regular 12" \
 --wrap --justify="center" \
 --margins=1 \
 --tail \
 --editable \
 --fore="#bb9af7" \
 --back="#16161E" \
 --listen \
 --auto-close \
 --auto-kill \
 --monitor \
 --text-info &

clear
case $CHOICE in
"1" )
    echo 'Запись разделов в fstab'
;;

"2" )
    echo 'Создание бэкапа в USB'
;;
esac
}

MENUDRIVE