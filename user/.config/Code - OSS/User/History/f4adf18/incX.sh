#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ -d $backup_drive/.config ]; then
    #sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    #sync
    #echo 'Синхронизация завершена'
    echo 'Не удалять содержимое т.к там пусто'
else
    #sudo rm -rf $backup_drive/.*
    #sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    #sync
    #echo 'Завершено'
    #sleep 2
    echo 'Удалять содержимое т.к там не пусто'
fi
