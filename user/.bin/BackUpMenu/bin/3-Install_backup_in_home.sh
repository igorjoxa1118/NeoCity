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



read -p "Имя пользователя: " username
read -p "Какой оконный менеджер? i3wm...bspwm: " dwm

backup_drive=/home/"$username"/Загрузки/USB_BACKUP_I3WM/"$dwm"
size=$(du -hSc "$backup_drive"/.[^.]* | tail -n1 | awk '{print $1}')

function deleted () {
    echo -e "${Red}Удаление старых файлов из домашнего каталога!"
    rm -rf /home/"$username"/.*
    echo -e "${Green}Удаление старых файлов из домашнего каталога завершено!"
    sleep 2
}

function install () {
    trap '' INT
    echo -e "${Yellow}Копирование файлов в '/home/"$username"/' началось. Необходимо скопировать примерно "$size""
    rsync -aAEHSXxr --stats -h --info=progress2 --info=name0 "$backup_drive"/.[^.]* /home/"$username"/
    sleep 2
    echo -e "${Blue}Синхронизация!"
    sync
    echo -e "${Purple}Синхронизация окончена!"
    sleep 2
}

function owner () {
    echo -e "${Cyan}Установка владельца"
    chown -R "$username":"$username" /home/"$username"/
    echo -e "${Red}Установка владельца завершена"
    sleep 2
}

if [ -d "/home/$username/Загрузки/USB_BACKUP_I3WM/.config" ]; then
    deleted
    clear
   
    install
    clear

    owner
    clear

    echo -e "${Green}Установка закончена. Приятного пользования!"
    sleep 2
else    
    install
    clear

    owner
    clear

    echo -e "${Yellow}Установка закончена. Приятного пользования!"
    sleep 2
fi
