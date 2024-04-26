#!/bin/bash

set -x

PWD="$(pwd)"
I3="$HOME/.config/i3"
POLYBAR="$HOME/.config/polybar"
ROFI="$HOME/.config/rofi"
PICOM="$HOME/.config/picom.conf"
BAK_DIR="$HOME/.config/config_bak"

mkdir $BAK_DIR

check() {
for dir in $I3 $POLYBAR $ROFI

do if [[ -d $dir ]] || [[ -f $PICOM ]]; then
  cp -r $dir $BAK_DIR
  cp -r $PICOM $BAK_DIR
   else
  echo "error"
fi
done
}


if [[ -s $BAK_DIR ]]; then 
  cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U *.zst
              else
              exit 1;
              fi
    fi
  else
rm -r $BAK_DIR
exit 1;
fi