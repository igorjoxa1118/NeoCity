#!/bin/bash

#set -x 

function menudrive () {
BACKTITLE="v.1.0"
MENU="Выберене нужный пункт:"
HEIGHT=30
WIDTH=60
CHOICE_HEIGHT=20

OPTIONS=(1 "Установить разделы в fstab"
         2 "Создать бэкап в USB"
         3 "Установить файлы в домашний каталог"
         4 "Удалить config файлы из домашнего каталога")

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
    sh ./bin/1-Install_part_in_fstab.sh
;;

"2" )
    sh ./bin/2-Backup_skel_to_USB.sh
;;

"3" )
    sh ./bin/3-Install_backup_in_home.sh
;;

"4" )
    sh ./bin/4-Deleted_home_config_skel.sh
;;
esac
}

menudrive