#!/bin/bash
#set -x

PWD="$(pwd)"

I3="$HOME/.config/i3"
POLYBAR="$HOME/.config/polybar"
ROFI="$HOME/.config/rofi"
PICOM="$HOME/.config/picom.conf"
DUNST="$HOME/.config/dunst"
GTK2="$HOME/.config/gtk-2.0"
GTK3="$HOME/.config/gtk-3.0"
XFCE4="$HOME/.config/xfce4"
HOME_gtk2="$HOME/.gtkrc-2.0"
HOME_zshrc="$HOME/.zshrc"

BAK_DIR="$HOME/.config/config_bak"

mkdir -p $BAK_DIR/home

check_dirs() {
for dir in $I3 $POLYBAR $ROFI $DUNST $GTK2 $GTK3 $XFCE4 $PICOM# Перечисляем каталоги в переменную "dir"

do if [[ -d $dir ]] || [[ -f $PICOM ]]; then # Делать, если существуют или каталоги
  mv $dir $BAK_DIR
  fi
done
}

check_files() {
for dir in $HOME_gtk2 $HOME_zshrc  # Перечисляем каталоги в переменную "dir"

do if [[ -f $dir ]]; then # Делать, если существуют или файлы
  mv $dir $BAK_DIR/home
  fi
done
}

if check_dirs && check_files;  then 
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