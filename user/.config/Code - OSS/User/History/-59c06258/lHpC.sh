#!/bin/bash
#set -x

store_drive=/home/vir0id/Загрузки/
store_drive_num=/dev/nvme0n1p5

backup_drive=/home/vir0id/Загрузки/USB_BACKUP_I3WM
backup_drive_num=/dev/sda1


UUID_store_drive="$(sudo blkid -s UUID -o value $store_drive_num)"
UUID_backup_drive="$(sudo blkid -s UUID -o value $backup_drive_num)"

echo "UUID="$UUID_store_drive" $store_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab
echo "UUID="$UUID_backup_drive" $backup_drive ext4 defaults 0 2" | sudo tee -a /etc/fstab