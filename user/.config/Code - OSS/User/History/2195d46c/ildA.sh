#!/bin/bash
#set -x

username=$USER

echo "Drive Partition number. ex 1..2..3"
read partnumber

echo "USB Partition number. ex sda1...adb1"
read usb

echo "Provide folder name for mounting Drive Partition"
read folder

echo "Provide folder name for mounting USB Partition"
read folder

store_drive=$folder
store_drive_num=/dev/nvme0n1p$partnumber

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM
backup_drive_num=/dev/$usb


UUID_store_drive="$(sudo blkid -s UUID -o value $store_drive_num)"
UUID_backup_drive="$(sudo blkid -s UUID -o value $backup_drive_num)"

#echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab
#echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab

echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" 
echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2"