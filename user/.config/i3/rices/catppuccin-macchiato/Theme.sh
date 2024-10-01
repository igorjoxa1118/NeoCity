#!/usr/bin/env bash

## Copyright (C) 2020-2024 Aditya Shakya <adi1090x@gmail.com>

read -r RICETHEME < "$HOME"/.config/i3/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_dir="$HOME/.config/i3"

# Terminate already running bar instances
killall -q polybar
killall -q eww

# # Fix backlight and network modules
# fix_modules() {
# 	if [[ -z "$CARD" ]]; then
# 		sed -i -e 's/backlight/bna/g' "$DIR"/config.ini
# 	elif [[ "$CARD" != *"intel_"* ]]; then
# 		sed -i -e 's/backlight/brightness/g' "$DIR"/config.ini
# 	fi

# 	if [[ "$INTERFACE" == e* ]]; then
# 		sed -i -e 's/network/ethernet/g' "$DIR"/config.ini
# 	fi
# }

# Launch the bar
launch_bar() {
	# Terminate already running bar instances
	killall -q polybar

	# Wait until the processes have been shut down
	while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

	# Launch the bar
	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "$rice_dir"/config.ini &
	done
}

# Execute functions
# if [[ ! -f "$RFILE" ]]; then
# 	fix_modules
# 	touch "$RFILE"
# fi	

# Firefox theme
set_firefox_theme() {
grep_ff=$(ls "$HOME"/.mozilla/firefox | grep default-release)
path_to_ff=""$HOME"/.mozilla/firefox/"$grep_ff"/chrome"
path_to_ff_themes=""$HOME"/.mozilla/FoxThemes"
theme_name="userChrome.css"

    if [ -d "$path_to_ff" ]; then
        cp -rf "$path_to_ff_themes"/"$RICETHEME"/chrome/"$theme_name" "$path_to_ff"
    else
        echo "Somthing wrong"
    fi
}

set_firefox_theme
launch_bar
