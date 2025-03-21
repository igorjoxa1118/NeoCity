#!/bin/sh

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

if [ "$(id -u)" -gt 0 ]; then
    echo -e "${Red}Скрипт должен быть запущен с sudo."
    exit 1
fi

. ./setup/setup-vars-welcome.sh

DIALOG_ERROR=254
export DIALOG_ERROR

$DIALOG --title "Привет мир!" --clear "$@" \
        --yesno "Привет! Этот скрипт позволит тебе: \n
1.Смонтировать раздел в папку Загрузки домашнего каталога \n
2.Смонтировать USB_BACKUP накопитель в папку Загрузки смонтированного ранее раздела  \n
3.Удалить старые файлы Skel из домашнего каталога \n
4.Установить файлы Skel из примонтированного USB_BACKUP накопителя" 15 61

retval=$?

. ./setup/report-welcome.sh
