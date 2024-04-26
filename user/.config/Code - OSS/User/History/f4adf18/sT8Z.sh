#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ `ls -al $backup_drive | wc -l` -eq 2 ]; then
    #sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    echo 'Пусто'
    sync
else
    sudo rm -rf $backup_drive/.*
    #sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
fi
