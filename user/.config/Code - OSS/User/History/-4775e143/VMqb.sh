#!/bin/bash

#set -x 

if [ "$(id -u)" != 0 ]; then
    echo "Необходимы права суперпользователя" >&2
	exit 1
fi

echo "Username"
read username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ `ls -al $backup_drive | wc -l` -eq 2 ]; then
    echo "Каталог пуст!"
else
    rm -rf $backup_drive/.*
    sync
fi

if [ `ls -al $backup_drive | wc -l` -le 3 ]; then
    rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
else
    echo "Каталог не пуст!!!!"
fi