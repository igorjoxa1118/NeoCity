#!/bin/bash
#set -x

lsblk

read -p "Имя пользователя для которого будут смонтированы разделы: " username

read -p "Номер раздела который нужно смонтировать. Пр. nvme0n1p1...5: " partnumber

read -p "Раздел USB который нужно смонтировать. Пр. sda1...sdb2: " usbpart

store_drive=/home/$username/Загрузки
store_drive_num=/dev/$partnumber


backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM
backup_drive_num=/dev/$usbpart


UUID_store_drive="$(sudo blkid -s UUID -o value $store_drive_num)"
UUID_backup_drive="$(sudo blkid -s UUID -o value $backup_drive_num)"

if [ ! -d $backup_drive ]; then
   mkdir $backup_drive
fi
#echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab
#echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab

echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" 
echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2"

while true; do
	read -rp "Перезагрузить компьютер? [y/N]: " yn
		case $yn in
			[Yy]* ) reboot;;
			[Nn]* ) exit;;
			* ) printf " Ошибка: допускается лишь 'y' или 'n'\n\n";;
		esac
    done