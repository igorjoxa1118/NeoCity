#!/usr/bin/bash

if killall eww; then 
 eww open --toggle main --config "${HOME}"/.config/i3/eww &
 else
  eww open --toggle main --config "${HOME}"/.config/i3/eww &
fi