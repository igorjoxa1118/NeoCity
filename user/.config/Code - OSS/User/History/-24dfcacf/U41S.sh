#!/usr/bin/bash

keybinds="/home/vir0id/Загрузки/repository/sources_test/keybinds"

function yad_main_display() { # Пустое окно yad, куда попадает вывод из StdOut/StdErr
 yad \
 --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
 --width=280 \
 --height=100 \
 --fontname="Iosevka Term Regular 12" \
 --wrap --justify="center" \
 --margins=1 \
 --tail \
 --editable \
 --fore="#bb9af7" \
 --back="#16161E" \
 --listen \
 --auto-close \
 --auto-kill \
 --monitor \
 --text-info & 
}

export -f yad_main_display

cat $keybinds | yad_main_display