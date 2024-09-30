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

CHOICE=$(dialog --clear \
                --backtitle "$BACKTITLE" \
                --title "$TITLE" \
                --menu "$MENU" \
                $HEIGHT $WIDTH \
                $CHOICE_HEIGHT \
                "${OPTIONS[@]}" \
                2>&1 >/dev/tty)

clear
case $CHOICE in
"1" )
    exec ./bin/1-Install_part_in_fstab.sh
;;

"2" )
    exec ./bin/2-Backup_skel_to_USB.sh
;;
esac
}

MENUDRIVE