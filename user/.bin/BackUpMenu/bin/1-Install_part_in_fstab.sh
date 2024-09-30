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

read -p "Имя пользователя для которого будут смонтированы разделы: " username

read -p "Номер раздела который нужно смонтировать. Пр. nvme0n1p1...5: " partnumber

read -p "Раздел USB который нужно смонтировать. Пр. sda1...sdb2: " usbpart

store_drive=/home/$username/Загрузки
store_drive_num=/dev/$partnumber


backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM
backup_drive_num=/dev/$usbpart


UUID_store_drive="$(blkid -s UUID -o value $store_drive_num)"
UUID_backup_drive="$(blkid -s UUID -o value $backup_drive_num)"

function owner () {
    chown -R "$username":"$username" "$backup_drive"
    echo -e "${Green}Установка владельца"
    sleep 2
}

if [ ! -d $backup_drive ]; then
   mkdir $backup_drive
fi
echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" | tee -a /etc/fstab
echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2" | tee -a /etc/fstab

while true; do
	read -rp "Перезагрузить компьютер? [y/N]: " yn
		case $yn in
			[Yy]* ) reboot;;
			[Nn]* ) exit;;
			* ) printf " Ошибка: допускается лишь 'y' или 'n'\n\n";;
		esac
    done