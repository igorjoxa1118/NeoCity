#!/bin/bash
#set -x 

check() {
for dir in "$del/pkg" "$del/src" "$del/Tokio_night" "$zst"
 do if [[ -d $dir ]] || [[ -f $zst ]]; then
   rm -rf $dir
   rm -rf $zst
   fi
done
}
check
mv $BAK_DIR/* $config_main
rm -d $BAK_DIR

