#!/bin/bash
#set -x 

# Regular Colors
Black='\033[0;30m'        # Black
Red='\033[0;31m'          # Red
Green='\033[0;32m'        # Green
Yellow='\033[0;33m'       # Yellow
Blue='\033[0;34m'         # Blue
Purple='\033[0;35m'       # Purple
Cyan='\033[0;36m'         # Cyan
White='\033[0;37m'        # White
# Underline
UBlack='\033[4;30m'       # Black
URed='\033[4;31m'         # Red
UGreen='\033[4;32m'       # Green
UYellow='\033[4;33m'      # Yellow
UBlue='\033[4;34m'        # Blue
UPurple='\033[4;35m'      # Purple
UCyan='\033[4;36m'        # Cyan
UWhite='\033[4;37m'       # White
# High Intensity
IBlack='\033[0;90m'       # Black
IRed='\033[0;91m'         # Red
IGreen='\033[0;92m'       # Green
IYellow='\033[0;93m'      # Yellow
IBlue='\033[0;94m'        # Blue
IPurple='\033[0;95m'      # Purple
ICyan='\033[0;96m'        # Cyan
IWhite='\033[0;97m'       # White

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