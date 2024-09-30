#!/bin/bash
#set -x

if [ "$(id -u)" != 0 ]; then
    echo "Необходимы права суперпользователя" >&2
	exit 1
fi

lsblk

read -p "Имя пользователя для которого будут смонтированы разделы: " username

read -p "Номер раздела который нужно смонтировать. Пр. nvme0n1p{1..2..3}: " partnumber

read -p "Раздел USB который нужно смонтировать. Пр. sda1...sdb1" usbpart

store_drive=/home/$username/Загрузки
store_drive_num=/dev/nvme0n1p$partnumber


backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM
backup_drive_num=/dev/$usbpart


UUID_store_drive="$(sudo blkid -s UUID -o value $store_drive_num)"
UUID_backup_drive="$(sudo blkid -s UUID -o value $backup_drive_num)"

if [ ! -d $backup_drive ]; then
   mkdir $backup_drive
else
   echo 'Folder exist'
fi
#echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab
#echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab
echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" 
echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2"