#!/bin/bash
set -x 

POL_DIR="$HOME/.config/polybar"
ROF_DIR="$HOME/.config/rofi"
PIC="$HOME/.config/picom.conf"
I3="$HOME/.config/i3/config"
I3_OLD="$HOME/.i3/config"
PWD="$(pwd)"

IF_HAVE_DIRS() {

if [[ -d $POL_DIR ]]; then
     mv $POL_DIR $POL_DIR.old
   if [[ -d $ROF_DIR ]]; then
     mv $ROF_DIR $ROF_DIR.old
    if [[ -f $PIC ]]; then
     mv $PIC $PIC.old
       if [[ -f $I3 ]]; then  
      mv $I3 $I3.old
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

}

IF_NO_DIRS () {

if [[ -d $POL_DIR ]] && [[ -d $ROF_DIR ]]; then
     echo "Polybar and Rofi directory exist"
      if [[ -f $PIC ]] && [[ -f $I3 ]]; then
     echo "Pocom file and i3 file exist"
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
      fi
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U $PWD*.zst
              else
              exit 1;
              fi

fi

}

IF_NO_DIRS

IF_HAVE_DIRS

if [[ -d $POL_DIR ]] && [[ -d $ROF_DIR ]]; then 