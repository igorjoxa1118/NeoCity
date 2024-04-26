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
for dir in $I3 $POLYBAR $ROFI $PICOM # Перечисляем каталоги в переменную "dir"

do if [[ -d $dir ]]; then # Делать, если существуют или каталоги, или файл picom
  mv $dir $BAK_DIR
fi
done
}

check

if [[ -s $BAK_DIR ]]; then 
  cd $PWD
      makepkg -s
              if dialog --yesno "Установить пакет?" 0 0; then
               sudo pacman -U *.zst
              else
              exit 1;
              fi
  else
rm -r $BAK_DIR
exit 1;
fi