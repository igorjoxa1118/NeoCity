#!/bin/bash

#set -x 

if [ ! -f /usr/bin/kitty ]; then
   sudo pacman -S kitty

else
   kitty -e ./menu.sh
fi