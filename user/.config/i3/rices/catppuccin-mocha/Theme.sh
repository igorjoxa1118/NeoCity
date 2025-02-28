#!/usr/bin/env bash

## Copyright (C) 2020-2024 Aditya Shakya <adi1090x@gmail.com>

read -r RICETHEME < "$HOME"/.config/i3/config.d/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_configd="$HOME/.config/i3/config.d"
i3_scr="$HOME/.config/i3/src"

# Terminate already running bar instances
killall -q polybar
killall -q eww

###--Start rice
theme_rofi_color() {
	sed -i "s|@import .*|@import \""colors/$RICETHEME.rasi"\"|g" "$HOME"/.config/i3/src/rofi-themes/RiceSelector.rasi
	sed -i "s|@import .*|@import \""colors/$RICETHEME.rasi"\"|g" "$HOME"/.config/i3/src/rofi-themes/NetManagerDM.rasi
}
theme_rofi_color

rofi_launcher_img() {
	if [ -f "$HOME/.config/i3/src/rofi-themes/launchpad_v4.rasi" ]; then
	 echo '' >  "$HOME/.config/i3/src/rofi-themes/launchpad_v4.rasi"
	 cat "$HOME/.config/i3/src/rofi-themes/img/$RICETHEME.rasi" > "$HOME/.config/i3/src/rofi-themes/launchpad_v4.rasi"
	fi
}
rofi_launcher_img

rofi_calendar_color() {
	if [ -f "$i3_scr/rofi-calendar/themes/colors.rasi" ]; then
	 echo '' >  "$i3_scr/rofi-calendar/themes/colors.rasi"
	 cat "$HOME/.config/i3/src/rofi-themes/colors/$RICETHEME.rasi" > "$i3_scr/rofi-calendar/themes/colors.rasi"
	fi
}
rofi_calendar_color

set_gtk_theme() {
	sed -i "s/gtk-theme-name=.*/gtk-theme-name="$RICETHEME"/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-theme-name=.*/gtk-theme-name="$RICETHEME"/g" "$HOME"/.config/gtk-4.0/settings.ini
    sed -i "s/gtk-theme-name=.*/gtk-theme-name="\"""$RICETHEME"""\"/g" "$HOME"/.gtkrc-2.0
}
set_gtk_theme

set_icons() {
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"TokyoNight-SE"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=TokyoNight-SE/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=TokyoNight-SE/g" "$HOME"/.config/gtk-4.0/settings.ini	
}
set_icons

set_cursor() {
	sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name="\"catppuccin-mocha-mauve-cursors"\"/g" "$HOME"/.gtkrc-2.0
	sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-mauve-cursors/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-mauve-cursors/g" "$HOME"/.config/gtk-4.0/settings.ini
}
set_cursor

# NetworkManager launcher
set_network_manager() {
	sed -i "$HOME/.config/i3/src/rofi-themes/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#1e1e2e;/' \
		-e '13s/\(background-alt: \).*/\1#2d3245;/' \
		-e '14s/\(foreground: \).*/\1#94e2d5;/' \
		-e '15s/\(selected: \).*/\1#565e82;/' \
		-e '16s/\(active: \).*/\1#89dceb;/' \
		-e '17s/\(urgent: \).*/\1#89dceb;/'
}
set_network_manager

# Reload terminal colors
set_term_config() {
	AL_CONFIG_DIR="$HOME/.config/alacritty"
	AL_RICE_DIR="$HOME/.config/i3/rices/$RICETHEME/alacritty"
		if [ -f $AL_CONFIG_DIR/alacritty.toml ]; then
			rm -rf $AL_CONFIG_DIR/*
			cp -rf $AL_RICE_DIR/* $AL_CONFIG_DIR
		fi
	KI_CONFIG_DIR="$HOME/.config/kitty"
	KI_RICE_DIR="$HOME/.config/i3/rices/$RICETHEME/kitty"
		if [ -f $KI_CONFIG_DIR/kitty.conf ]; then
			cp -rf $KI_RICE_DIR/kitty.conf $KI_CONFIG_DIR
		else
			cp -rf $HOME/.config/i3/rices/$RICETHEME/kitty/kitty.conf $HOME/.config/kitty/
		fi
}
set_term_config


# Firefox theme
firefox_profiles() {
	THEME_DIR="$HOME/.mozilla/FoxThemes"
	DEST_DIR="$HOME/.mozilla/firefox/"

if [[ $(grep '\[Profile[^0]\]' "$HOME"/.mozilla/firefox/profiles.ini) ]]; then 
	PROFPATH=$(grep -E '^\[Profile|^Path|^Default' "$HOME"/.mozilla/firefox/profiles.ini | grep -1 '^Default=1' | grep '^Path' | cut -c6-)
	cp -rf "$THEME_DIR"/* "$DEST_DIR"/"$PROFPATH"
else 
	PROFPATH=$(grep 'Path=' "$HOME"/.mozilla/firefox/profiles.ini | sed 's/^Path=//')
	cp -rf "$THEME_DIR"/* "$DEST_DIR"/"$PROFPATH"
fi
}
firefox_profiles

# Set dunst config
set_dunst_config() {
dunst_path=""$HOME"/.config/i3/rices/$RICETHEME/dunst/dunstrc"
       if [ -f "$dunst_path" ]; then
         cp -rf "$dunst_path" ~/.config/dunst/
       else
         echo "Color file not exist!"
       fi
}
set_dunst_config

###---Global. Change colors for Tabbed
tabbed_settings() {
tabbed_path=""$HOME"/.config/i3/rices/$RICETHEME/tabbed/colors"
       if [ -f "$tabbed_path" ]; then
         cp -rf "$tabbed_path" "$i3_configd"
       else
         echo "Color file not exist!"
       fi
}
tabbed_settings

xresources_color() {
	if [ -f "$HOME/.Xresources.d/colors" ]; then
	 echo '' >  "$HOME/.Xresources.d/colors"
	 cat "$HOME/.Xresources.d/themes/$RICETHEME" > "$HOME/.Xresources.d/colors"
	 xrdb  ~/.Xresources
	fi
}
xresources_color

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))
#xrdb -merge $HOME/.Xresources.d/themes/mocha.Xresources
# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q secondary -c "${rice_dir}"/config.ini &
	done
}
launch_bars
