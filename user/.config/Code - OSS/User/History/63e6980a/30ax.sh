#!/bin/bash
set -x 

POL_DIR="$HOME/.config/polybar"
ROF_DIR="$HOME/.config/rofi"
PIC="$HOME/.config/picom.conf"
I3="$HOME/.config/i3/config"
I3_OLD="$HOME/.i3/config"
PWD="$(pwd)"

if [[ -d $POL_DIR ]]; then
     mv $POL_DIR $POL_DIR.old
      else
  if [[ -d $ROF_DIR ]]; then
     mv $ROF_DIR $ROF_DIR.old
      else
    if [[ -f $PIC ]]; then
     mv $PIC $PIC.old
      else
      if [[ -f $I3 ]]; then  
      mv $I3 $I3.old
      cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U $PWD*.zst
              else
              exit 1;
              fi
      else
        if [[ -f $I3_OLD ]]; then
         rm -r "$HOME/.i3/"
        else
      mv $I3_OLD $I3_OLD.old
      cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U $PWD*.zst
              else
              exit 1;
              fi
        fi
      fi
    fi
  fi
fi