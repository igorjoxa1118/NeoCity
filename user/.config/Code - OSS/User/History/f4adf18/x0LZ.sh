#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ -d "/home/$username/Загрузки/USB_BACKUP_I3WM/.config" ]; then
    sudo rm -rf $backup_drive/.*
    sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
    echo 'Завершено'
    sleep 2
else
    sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
    echo 'Синхронизация завершена'
    sleep 2
fi
