#!/bin/bash
#set -x 
del="$(pwd)"
zst=$(ls | grep Tokio_night)
BAK_DIR="$HOME/.config/config_bak"
config_main="$HOME/.config"

check() {
for dir in "$del/pkg" "$del/src" "$del/Tokio_night" "$zst"
 do if [[ -d $dir ]] || [[ -f $zst ]]; then
   rm -rf $dir
   rm -rf $zst
   fi
done
}
check

mv -f $BAK_DIR/* $config_main
mv -f $BAK_DIR/home/.* $HOME
rm -d $BAK_DIR

