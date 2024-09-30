#!/bin/bash

#set -x 

if [ ! -f /usr/bin/kitty ]; then
   sudo pacman -S kitty
fi

kitty -e ./bin/menu.sh