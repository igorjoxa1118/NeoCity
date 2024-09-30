#!/bin/bash

#set -x 

if [ "$(id -u)" != 0 ]; then
    echo "Необходимы права суперпользователя" >&2
	exit 1
fi

echo "Username"
read username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ `ls -al $backup_drive | wc -l` -gt 2 ]; then
    rm -rf $backup_drive/.*
    sync
else
    echo "Каталог пуст!"
fi

if [ `ls -al $backup_drive | wc -l` -eq 2 ]; then
    rsync -aAEHSXxrv ~/.[^.]* $backup_drive
    sync
else
    echo "Каталог не пуст!"
fi