#!/bin/bash
set -x

DIALOG() {
USER_NAME=$(dialog --stdout --title "Username?" --inputbox "Username:" 14 48)
I3_CONF=$(dialog --stdout --title "$HOME_DIR "/" " --inputbox "Where is i3 config file?:" 14 48)
POLYBAR_DIR=$(dialog --stdout --title "/home/$USER_NAME/.config "/" " --inputbox "Where is polybar directory?:" 14 48)
ROFI_DIR=$(dialog --stdout --title "/home/$USER_NAME/.config "/" " --inputbox "Where is rofi directory?:" 14 48)
PICOM=$(dialog --stdout --title "/home/$USER_NAME/.config "/" " --inputbox "Whereis picom.config file?:" 14 48)
HOME_DIR="/home/$USER_NAME"


}

DIALOG