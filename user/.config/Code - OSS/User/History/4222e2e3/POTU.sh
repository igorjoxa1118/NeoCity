#!/bin/bash
set -x 

del="$(cd $PWD)"
zst="*.zst"

check() {
for dir in "$del/pkg" "$del/src" "$del/Tokio_night" "$zst"
   rm -rf $dir
done
}