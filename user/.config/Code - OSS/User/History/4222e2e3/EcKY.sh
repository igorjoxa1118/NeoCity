#!/bin/bash
set -x 

POL_DIR="$HOME/.config/polybar"
ROF_DIR="$HOME/.config/rofi"
PIC="$HOME/.config/picom.conf"
I3="$HOME/.config/i3/config"
I3_OLD="$HOME/.i3/config"
PWD="$(pwd)"

IF_HAVE_DIRS() {

if [[ -d $POL_DIR.old ]]; then
     mv $POL_DIR.old $POL_DIR
  if [[ -d $ROF_DIR.old ]]; then
     mv $ROF_DIR.old $ROF_DIR
    if [[ -f $PIC.old ]]; then
     mv $PIC.old $PIC
       if [[ -f $I3.old ]]; then  
        mv $I3.old $I3
        cd $PWD
        rm -rf pkg src Tokio_night *.zst
        else
        exit 1;
       fi
    fi
  fi
fi

}

IF_NO_DIRS() {
if [[ ! -d $POL_DIR.old ]] || [[ ! -d $POL_DIR ]]; then
   cd $PWD
   rm -rf pkg src Tokio_night *.zst
fi
}

if [[ -d $POL_DIR ]] && [[ -d $ROF_DIR ]]; then 
  IF_HAVE_DIRS
 else
  IF_NO_DIRS
fi