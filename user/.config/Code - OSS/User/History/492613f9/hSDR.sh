#!/bin/bash
set -x

DIALOG() {
USER_NAME=$(dialog --stdout --title "Username?" --inputbox "Username:" 14 48)
I3_CONF=$(dialog --stdout --title "$HOME_DIR "/" " --inputbox "Where is i3 config file?:" 14 48)
POLYBAR_DIR=$(dialog --stdout --title "/home/$USER_NAME/.config "/" " --inputbox "Where is polybar directory?:" 14 48)
ROFI_DIR=$(dialog --stdout --title "/home/$USER_NAME/.config "/" " --inputbox "Where is rofi directory?:" 14 48)
PICOM=$(dialog --stdout --title "/home/$USER_NAME/.config "/" " --inputbox "Whereis picom.config file?:" 14 48)
HOME_DIR="/home/$USER_NAME"
PWD="$(pwd)"

if [[ -d $POLYBAR_DIR ]]; then
     mv $POLYBAR_DIR $POLYBAR_DIR.old
   if [[ -d $ROFI_DIR ]]; then
     mv $ROFI_DIR $ROFI_DIR.old
    if [[ -f $PICOM ]]; then
     mv $PICOM $PICOM.old
       if [[ -f $I3_CONF ]]; then  
      mv $I3_CONF $I3_CONF.old
      cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U $pwd*.zst
              else
              exit 1;
              fi
      
      fi
    fi
  fi
fi

}

DIALOG