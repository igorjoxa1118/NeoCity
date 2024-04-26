#!/bin/bash
set -x 

POL_DIR="$HOME/.config/polybar"
ROF_DIR="$HOME/.config/rofi"
PIC="$HOME/.config/picom.conf"
I3="$HOME/.config/i3/config"
I3_OLD="$HOME/.i3/config"
PWD="$(pwd)"

RETURN() {

if [[ -d $POL_DIR ]]; then
     if dialog --yesno "Сделать копию каталога polybar?" 0 0; then
     mv $POL_DIR $POL_DIR.old
      else
  if [[ -d $ROF_DIR ]]; then
  if dialog --yesno "Сделать копию каталога rofi?" 0 0; then
     mv $ROF_DIR $ROF_DIR.old
     else
              exit 1;
              fi
      else
    if [[ -f $PIC ]]; then
    if dialog --yesno "Сделать копию файла picom.conf?" 0 0; then
     mv $PIC $PIC.old
          else
              exit 1;
              fi
      else
      if [[ -f $I3 ]]; then
      if dialog --yesno "Сделать копию файла /i3/config?" 0 0; then  
      mv $I3 $I3.old
                else
              exit 1;
              fi
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
      fi
    fi
  fi
fi

}