#!/bin/bash
set -x 
del="$(pwd)"
zst="*.zst"

check() {
for dir in "$del/pkg" "$del/src" "$del/Tokio_night" "$zst"
 do if [[ -d $dir ]] || [[ -f $zst ]]; then
   rm -rf $dir
    else
   echo "Noting to do"
   fi
done
}
check