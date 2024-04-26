#!/bin/bash

set -x

PWD="$(pwd)"
I3="$HOME/.config/i3"
POLYBAR="$HOME/.config/polybar"
ROFI="$HOME/.config/rofi"
PICOM="$HOME/.config/picom.conf"
BAK_DIR="$HOME/.config/config_bak"


for dir in $I3 $POLYBAR $ROFI

do if [[ -d $dir ]] || [[ -f $PICOM ]]; then
  echo "yes dirs"
   else
  echo "error"
fi
done