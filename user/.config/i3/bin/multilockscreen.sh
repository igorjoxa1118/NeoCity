#!/bin/sh

IMG="$HOME/.wallpapers/Hypri3/Tokyo-Night/lowpoly_street.png"

if [[ $(command -v  multilockscreen) ]]; then
  if [[ ! -d $HOME/.cache/multilock ]]; then
    multilockscreen -u $IMG --blur 0.5
  fi

  multilockscreen -l blur
fi
