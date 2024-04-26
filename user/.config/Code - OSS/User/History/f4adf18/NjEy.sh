#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ 'find /home/vir0id/Загрузки/USB_BACKUP_I3WM -name ".*"' ]; then
    #sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    echo 'Пусто'
    sync
else
    sudo rm -rf $backup_drive/.*
    #sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
    echo 'Не пусто'
    sleep 2
fi
