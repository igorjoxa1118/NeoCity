#!/usr/bin/env bash

## Copyright (C) 2020-2024 Aditya Shakya <adi1090x@gmail.com>

read -r RICETHEME < "$HOME"/.config/i3/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_dir="$HOME/.config/i3"

# Terminate already running bar instances
killall -q polybar
killall -q eww

###--Start rice

set_gtk_theme() {
	sed -i "s/gtk-theme-name=.*/gtk-theme-name="$RICETHEME"/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-theme-name=.*/gtk-theme-name="$RICETHEME"/g" "$HOME"/.config/gtk-4.0/settings.ini
    sed -i "s/gtk-theme-name=.*/gtk-theme-name="\"""$RICETHEME"""\"/g" "$HOME"/.gtkrc-2.0
}

set_icons() {
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Catppuccin-Macchiato"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Catppuccin-Macchiato/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Catppuccin-Macchiato/g" "$HOME"/.config/gtk-4.0/settings.ini	
}

set_cursor() {
	sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name="\"catppuccin-mocha-teal-cursors"\"/g" "$HOME"/.gtkrc-2.0
	sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-teal-cursors/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-teal-cursors/g" "$HOME"/.config/gtk-4.0/settings.ini
}

# NetworkManager launcher
set_network_manager() {
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#24273a;/' \
		-e '13s/\(background-alt: \).*/\1#2d3245;/' \
		-e '14s/\(foreground: \).*/\1#94e2d5;/' \
		-e '15s/\(selected: \).*/\1#565e82;/' \
		-e '16s/\(active: \).*/\1#89dceb;/' \
		-e '17s/\(urgent: \).*/\1#89dceb;/'
}

set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/\".*:class_g = 'Xfce4-terminal'\"/\"98:class_g = 'Xfce4-terminal'\"/g" \
		-e "s/\".*:class_g = 'Deadbeef'\"/\"98:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g = 'XTerm'\"/\"98:class_g = 'XTerm'\"/g" \
		-e "s/\".*:class_g = 'kitty'\"/\"98:class_g = 'kitty'\"/g" \
		-e "s/\".*:class_g = 'TelegramDesktop'\"/\"98:class_g = 'TelegramDesktop'\"/g" \
		-e "s/\".*:class_g =  'discord'\"/\"98:class_g = 'discord'\"/g" \
		-e "s/\".*:class_g *= 'Thunar'\"/\"98:class_g = 'Thunar'\"/g" \
		-e "s/\".*:class_g *= 'Caja'\"/\"98:class_g = 'Caja'\"/g" \
		-e "s/\".*:class_g *= 'Rofi'\"/\"98:class_g = 'Rofi'\"/g" \
		-e "s/\".*:class_g *= 'Conky'\"/\"98:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g *= 'Nm-applet'\"/\"98:class_g = 'Nm-applet'\"/g" \
		-e "s/\".*:class_g *= 'NetworkManager'\"/\"98:class_g = 'NetworkManager'\"/g" \
		-e "s/\".*:class_g *= 'qBittorrent'\"/\"98:class_g = 'qBittorrent'\"/g" \
		-e "s/\".*:class_g *= 'transmission-gtk'\"/\"98:class_g = 'transmission-gtk'\"/g" \
		-e "s/\".*:class_g *= 'Polybar'\"/\"100:class_g = 'Polybar'\"/g" \
		-e "s/\".*:class_g *= 'jgmenu_run'\"/\"98:class_g = 'jgmenu_run'\"/g" \
		-e "s/\".*:class_g *= 'code-oss'\"/\"98:class_g = 'code-oss'\"/g"
}

# Reload terminal colors
set_term_config() {
	AL_CONFIG_DIR="$HOME/.config/alacritty"
	AL_RICE_DIR="$HOME/.config/i3/rices/catppuccin-frappe/alacritty"
		if [ -f $AL_CONFIG_DIR/colors.toml ]; then
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

# Set dunst config
set_dunst_config() {
	dunst_config_file="$HOME/.config/i3/dunstrc"
	echo -n "" > "$dunst_config_file"
	cat >>"$dunst_config_file" <<-_EOF_
###--- Catppuccin-macchiato

[global]
frame_width= 1
frame_color = "#f5a97f"
font = MesloLGS NF 10

[urgency_low]
timeout = 3
background = "#24273a"
foreground = "#cad3f5"

[urgency_normal]
timeout = 5
background = "#24273a"
foreground = "#b8c0e0"

[urgency_critical]
timeout = 0
background = "#24273a"
foreground = "#a5adcb"
	_EOF_
}

###---Global. Change colors for Tabbed
tabbed_settings() {
tabbed_path=""$HOME"/.config/i3/rices/$RICETHEME/tabbed"
       if [ -f "$tabbed_path"/colors ]; then
         cp -rf "$tabbed_path"/colors "$i3_dir"
       else
         echo "Color file not exist!"
       fi
}

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))
#xrdb -merge $HOME/.Xresources.d/themes/mocha.Xresources
# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q top-1 -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q top-2 -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q top-3 -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q bottom-1 -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q bottom-2 -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q bottom-3 -c "${rice_dir}"/config.ini &
	done
}

launch_bars
set_gtk_theme
set_icons
set_cursor
set_network_manager
set_picom_config
firefox_profiles
set_dunst_config
tabbed_settings
set_term_config