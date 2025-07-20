#!/usr/bin/bash

read -r RICETHEME < "$HOME"/.config/i3/config.d/.rice

if killall eww; then 
 eww open --toggle main --config "${HOME}"/.config/i3/rices/$RICETHEME/eww &
 else
  eww open --toggle main --config "${HOME}"/.config/i3/rices/$RICETHEME/eww &
fi