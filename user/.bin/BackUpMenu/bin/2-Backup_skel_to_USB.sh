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

lsblk

read -p "Имя пользователя: " username
read -p "Раздел USB(sda1), куда нужно сделать бэкап. Пр. sda1, sda2...: " dwm

if [[ "$dwm" == "sda1" ]]; then
UUID_sda="$(blkid -s UUID -o value /dev/sda1)"
fi

if [[ "$dwm" == "sda2" ]]; then
UUID_sda="$(blkid -s UUID -o value /dev/sda2)"
fi

if [[ "$dwm" == "sda3" ]]; then
UUID_sda="$(blkid -s UUID -o value /dev/sda3)"
fi

if [[ "$dwm" == "sda4" ]]; then
UUID_sda="$(blkid -s UUID -o value /dev/sda4)"
fi

backup_drive=/run/media/"$username"/"$UUID_sda"
size=$(du -hSc /home/"$username"/.[^.]* | tail -n1 | awk '{print $1}')


if [ -d ""$backup_drive"/.config" ]; then
    echo -e "${Purple}Удаление файлов из USB накопителя."
    sudo rm -rf "$backup_drive"/.*
    sync
    sleep 2

    echo -e "${Cyan}Копирование файлов в USB накопитель. Необходимо скопировать примерно "$size""
    sudo rsync -aAEHSXxr --stats -h --info=progress2 --info=name0 --exclude=".cache/*" /home/"$username"/.[^.]* "$backup_drive"
    sync
    sleep 2

    echo -e "${Blue}Синхронизация! Подождите!"
    sync
    sleep 2
    echo -e "${Yellow}Синхронизация завершена!"
    sleep 2
elif [ ! -d ""$backup_drive"/.config" ]; then
    echo -e "${Green}Копирование файлов в USB накопитель. Необходимо скопировать примерно "$size""
    sudo rsync -aAEHSXxr --stats -h --info=progress2 --info=name0 --exclude=".cache/*" /home/"$username"/.[^.]* "$backup_drive"
    sync
    sleep 2

    echo -e "${Red}Синхронизация! Подождите!"
    sync

    echo -e "${Purple}Синхронизация завершена!"
    sleep 2
else
    echo -e "${Red}Неудачное копирование! Что-то пошло не так!"
fi
