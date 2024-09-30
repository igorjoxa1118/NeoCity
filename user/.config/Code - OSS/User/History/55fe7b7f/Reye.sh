#!/usr/bin/env bash
set -x
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Luv"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Luv/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Luv/g" "$HOME"/.config/gtk-4.0/settings.ini	
}

set_cursor() {
	sed -i "s/gtk-cursor-theme-name=.*/gtk-icon-theme-name="\"Vimix"\"/g" "$HOME"/.gtkrc-2.0
	sed -i "s/gtk-cursor-theme-name=.*/gtk-icon-theme-name=Vimix/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-cursor-theme-name=.*/gtk-icon-theme-name=Vimix/g" "$HOME"/.config/gtk-4.0/settings.ini
}

# NetworkManager launcher
set_network_manager() {
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#232735;/' \
		-e '13s/\(background-alt: \).*/\1#2d3245;/' \
		-e '14s/\(foreground: \).*/\1#7C84A8;/' \
		-e '15s/\(selected: \).*/\1#565e82;/' \
		-e '16s/\(active: \).*/\1#00A9A5;/' \
		-e '17s/\(urgent: \).*/\1#00A9A5;/'
}

set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/\".*:class_g = 'Xfce4-terminal'\"/\"100:class_g = 'Xfce4-terminal'\"/g" \
		-e "s/\".*:class_g = 'Deadbeef'\"/\"100:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g = 'XTerm'\"/\"100:class_g = 'XTerm'\"/g" \
		-e "s/\".*:class_g = 'kitty'\"/\"100:class_g = 'kitty'\"/g" \
		-e "s/\".*:class_g = 'TelegramDesktop'\"/\"100:class_g = 'TelegramDesktop'\"/g" \
		-e "s/\".*:class_g *= 'Thunar'\"/\"100:class_g = 'Thunar'\"/g" \
		-e "s/\".*:class_g *= 'Caja'\"/\"100:class_g = 'Caja'\"/g" \
		-e "s/\".*:class_g *= 'Rofi'\"/\"100:class_g = 'Rofi'\"/g" \
		-e "s/\".*:class_g *= 'Conky'\"/\"100:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g *= 'Nm-applet'\"/\"100:class_g = 'Nm-applet'\"/g" \
		-e "s/\".*:class_g *= 'NetworkManager'\"/\"100:class_g = 'NetworkManager'\"/g" \
		-e "s/\".*:class_g *= 'qBittorrent'\"/\"100:class_g = 'qBittorrent'\"/g" \
		-e "s/\".*:class_g *= 'transmission-gtk'\"/\"100:class_g = 'transmission-gtk'\"/g" \
		-e "s/\".*:class_g *= 'Polybar'\"/\"100:class_g = 'Polybar'\"/g" \
		-e "s/\".*:class_g *= 'jgmenu_run'\"/\"100:class_g = 'jgmenu_run'\"/g" \
		-e "s/\".*:class_g *= 'code-oss'\"/\"100:class_g = 'code-oss'\"/g"
}

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "${rice_dir}"/config.ini &
		#MONITOR=$mon polybar -q main -c ~/.config/i3/rices/tealize/polybar/config.ini &
	done
}

launch_bars
set_gtk_theme
set_icons
set_cursor
set_network_manager
set_picom_config