#!/bin/bash

#set -x 

read -p "Имя пользователя: " username

backup_drive=/home/$username/Загрузки/USB_BACKUP_I3WM

function deleted () {
    cd /home/"$username"/test && rm -rf .*
}

function install () {
    trap '' INT
    sudo rsync -aAEHSXxrv "$backup_drive"/.[^.]* /home/"$username"/
    sync
}

function owner () {
    sudo chown -R "$username":"$username" /home/"$username"/
}

if [ -d "/home/$username/Загрузки/USB_BACKUP_I3WM/.config" ]; then
    echo 'Удаление старых файлов из домашнего каталога!'
    sleep 2
    deleted
    clear

    echo 'Начало установки файлов в домашний каталог!'
    sleep 2    
    install
    clear

    echo 'Установка владельца'
    sleep 2
    owner
    clear

    echo 'Завершено'
    sleep 2
else
    echo 'Что-то пошло не так. Наверное в источнике нету файлов конфигураций!'
    sleep 2
fi
