#!/bin/bash
set -x 
del="$(pwd)"
zst=$(ls | grep Tokio_night)

check() {
for dir in "$del/pkg" "$del/src" "$del/Tokio_night" "$zst"
 do if [[ -d $dir ]] || [[ -f $zst ]]; then
   rm -rf $dir
   rm -rf $zst
    else
   echo "Noting to do"
   fi
done
}
check