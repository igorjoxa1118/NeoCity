#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

if [ -d "/home/$username/Загрузки/USB_BACKUP_I3WM/.config" ]; then
    sudo rm -rf $backup_drive/.*
    . ./setup-vars
    . ./setup-tempfile

ls -1 "$backup_drive">$tempfile
(
while true
do
read text
test -z "$text" && break
ls -ld "$text" || break
sleep 1
done <$tempfile
) |

$DIALOG --title "PROGRESS" "$@" --progressbox 20 70

retval=$?
. ./report-button
    sync
    echo 'Завершено'
    sleep 2
else
    sudo rsync -aAEHSXxrv /home/$username/.[^.]* $backup_drive
    sync
    echo 'Синхронизация завершена'
    sleep 2
fi
