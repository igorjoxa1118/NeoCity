#!/bin/bash

#set -x 

MENUDRIVE() {
BACKTITLE="v.1.0"
MENU="Выберене нужный пункт:"
HEIGHT=30
WIDTH=60
CHOICE_HEIGHT=20

OPTIONS=(1 "Синхронизировать домашний каталог"
         2 "Создать резервную копию root+home"
         3 "Удалить резервные копии"
         4 "Создать архив sys.tar.gz"
         5 "Записать архив sys.tar.gz в Drive"
         6 "Извлечь архив в /"
         7 "Установка программного обеспечения")

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
;;
esac
}