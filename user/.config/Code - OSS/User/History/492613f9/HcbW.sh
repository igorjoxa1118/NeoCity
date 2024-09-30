#!/bin/bash
set -x

DIALOG() {
username=$(dialog --stdout --title "Пользователь, чъя копия будет создана?" --inputbox "Имя пользвателя:" 14 48)
FULLBACKUP=$(dialog --stdout --title "Все пути должны начинаться и заканчиваться "/" " --inputbox "Куда сделать резервную копию?:" 14 48)
homedir="/home/$username"

if [ -z $username ]; then
   DIALOG
   elif [ -z $FULLBACKUP ]; then
   DIALOG
   fi
}

DIALOG