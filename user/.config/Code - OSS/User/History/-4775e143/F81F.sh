#!/bin/bash

#set -x 

if [ "$(id -u)" != 0 ]; then
    echo "Необходимы права суперпользователя" >&2
	exit 1
fi

echo "Username"
read username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ $(find -type f -name '*.*') ]; then
    rm -rf $backup_drive/.*
    sync
else
    echo "Каталог пуст!"
fi

if [ $(find -type f -name '*.*') ]; then
    rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
else
    echo "Каталог не пуст!!!!"
fi