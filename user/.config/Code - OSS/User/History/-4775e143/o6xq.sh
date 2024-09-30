#!/bin/bash

#set -x 

if [ "$(id -u)" != 0 ]; then
    echo "Необходимы права суперпользователя" >&2
	exit 1
fi

username=$USER
backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ `ls -al $backup_drive | wc -l` -gt 2 ]; then
    rm -rf $backup_drive/.*
    sync
else
    echo "Каталог не пуст!"
fi

if [ `ls $backup_drive | wc -l` -gt 0 ]; then
    rsync -aAEHSXxrv ~/.[^.]* $backup_drive
    sync
else
    echo "Каталог не пуст!"
fi