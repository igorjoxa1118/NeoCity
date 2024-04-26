#!/bin/bash
set -x

DIALOG() {
username=$(dialog --stdout --title "Пользователь, чъя копия будет создана?" --inputbox "Имя пользвателя:" 14 48)
I3_CONF=$(dialog --stdout --title "Все пути должны начинаться и заканчиваться "/" " --inputbox "Куда сделать резервную копию?:" 14 48)
POLYBAR_DIR=$(dialog --stdout --title "Все пути должны начинаться и заканчиваться "/" " --inputbox "Куда сделать резервную копию?:" 14 48)
ROFI_DIR=$(dialog --stdout --title "Все пути должны начинаться и заканчиваться "/" " --inputbox "Куда сделать резервную копию?:" 14 48)
PICOM=$(dialog --stdout --title "Все пути должны начинаться и заканчиваться "/" " --inputbox "Куда сделать резервную копию?:" 14 48)
homedir="/home/$username"


}

DIALOG