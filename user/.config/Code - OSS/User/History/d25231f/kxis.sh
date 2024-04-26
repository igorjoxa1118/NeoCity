#!/bin/bash
set -x 

POL_DIR="$HOME/.config/polybar"
ROF_DIR="$HOME/.config/rofi"
PIC="$HOME/.config/picom.conf"
I3="$HOME/.config/i3/config"
I3_OLD="$HOME/.i3/config"
PWD="$(pwd)"

IF_NO_DIRS() {

if [[ -d $POL_DIR ]]; then
     echo "Polybar directory exist"
      elif [[ -d $ROF_DIR ]]; then
     echo "Rofi directory exist"
      elif [[ -f $PIC ]]; then
     echo "pocon file exist"
      elif [[ -f $I3 ]]; then  
      echo "i3 config file exist"
      cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U $PWD*.zst
              else
              exit 1;
              fi
      else
        if [[ -f $I3_OLD ]]; then
         mv "$HOME/.i3/" "$HOME/.i3.old/"
        else
      cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U $PWD*.zst
              else
              exit 1;
              fi

fi

}

IF_NO_DIRS