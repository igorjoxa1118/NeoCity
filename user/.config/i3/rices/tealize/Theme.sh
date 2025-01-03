#!/usr/bin/env bash

## Copyright (C) 2020-2024 Aditya Shakya <adi1090x@gmail.com>

read -r RICETHEME < "$HOME"/.config/i3/config.d/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_dir="$HOME/.config/i3/config/d"

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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Obsidian-Teal"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Obsidian-Teal/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Obsidian-Teal/g" "$HOME"/.config/gtk-4.0/settings.ini	
}

set_cursor() {
	sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name="\"catppuccin-mocha-teal-cursors"\"/g" "$HOME"/.gtkrc-2.0
	sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-teal-cursors/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-teal-cursors/g" "$HOME"/.config/gtk-4.0/settings.ini
}

# NetworkManager launcher
set_network_manager() {
	sed -i "$HOME/.config/i3/src/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#232735;/' \
		-e '13s/\(background-alt: \).*/\1#2d3245;/' \
		-e '14s/\(foreground: \).*/\1#7C84A8;/' \
		-e '15s/\(selected: \).*/\1#565e82;/' \
		-e '16s/\(active: \).*/\1#00A9A5;/' \
		-e '17s/\(urgent: \).*/\1#00A9A5;/'
}

set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/\".*:class_g = 'Xfce4-terminal'\"/\"90:class_g = 'Xfce4-terminal'\"/g" \
		-e "s/\".*:class_g = 'Deadbeef'\"/\"90:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g = 'XTerm'\"/\"90:class_g = 'XTerm'\"/g" \
		-e "s/\".*:class_g = 'kitty'\"/\"100:class_g = 'kitty'\"/g" \
		-e "s/\".*:class_g = 'TelegramDesktop'\"/\"90:class_g = 'TelegramDesktop'\"/g" \
		-e "s/\".*:class_g =  'discord'\"/\"90:class_g = 'discord'\"/g" \
		-e "s/\".*:class_g *= 'Thunar'\"/\"90:class_g = 'Thunar'\"/g" \
		-e "s/\".*:class_g *= 'Caja'\"/\"90:class_g = 'Caja'\"/g" \
		-e "s/\".*:class_g *= 'Rofi'\"/\"90:class_g = 'Rofi'\"/g" \
		-e "s/\".*:class_g *= 'Conky'\"/\"90:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g *= 'Nm-applet'\"/\"90:class_g = 'Nm-applet'\"/g" \
		-e "s/\".*:class_g *= 'NetworkManager'\"/\"90:class_g = 'NetworkManager'\"/g" \
		-e "s/\".*:class_g *= 'qBittorrent'\"/\"90:class_g = 'qBittorrent'\"/g" \
		-e "s/\".*:class_g *= 'transmission-gtk'\"/\"90:class_g = 'transmission-gtk'\"/g" \
		-e "s/\".*:class_g *= 'Polybar'\"/\"90:class_g = 'Polybar'\"/g" \
		-e "s/\".*:class_g *= 'code-oss'\"/\"90:class_g = 'code-oss'\"/g"
}

# Reload terminal colors
set_term_config() {
	cat >"$HOME"/.config/alacritty/rice-colors.toml <<EOF
# (Tokyo Night) color scheme for Emilia Rice

# Default colors
[colors.primary]
background = "#232735"
foreground = "#7C84A8"

# Cursor colors
[colors.cursor]
cursor = "#7C84A8"
text = "#232735"

# Normal colors
[colors.normal]
black = "#15161e"
blue = "#7C84A8"
cyan = "#7dcfff"
green = "#9ece6a"
magenta = "#bb9af7"
red = "#f7768e"
white = "#a9b1d6"
yellow = "#e0af68"

# Bright colors
[colors.bright]
black = "#414868"
blue = "#7C84A8"
cyan = "#7dcfff"
green = "#9ece6a"
magenta = "#bb9af7"
red = "#f7768e"
white = "#7C84A8"
yellow = "#e0af68"
EOF
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Emilia rice
\$bg: #232735;
\$bg-alt: #222330;
\$fg: #7C84A8;
\$black: #414868;
\$lightblack: #262831;
\$red: #f7768e;
\$blue: #7C84A8;
\$cyan: #7dcfff;
\$magenta: #bb9af7;
\$green: #9ece6a;
\$yellow: #e0af68;
\$archicon: #0f94d2;
EOF
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/src/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"MesloLGS NF Regular 10";/' \
		-e 's/\(background: \).*/\1#232735;/' \
		-e 's/\(background-alt: \).*/\1#2d3245E0;/' \
		-e 's/\(foreground: \).*/\1#7C84A8;/' \
		-e 's/\(foreground-alt: \).*/\1#232735;/' \
		-e 's/\(selected: \).*/\1#00A9A5;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"
}

# Firefox theme
set_firefox_theme() {
grep_ff=$(ls "$HOME"/.mozilla/firefox | grep default-release)
path_to_ff=""$HOME"/.mozilla/firefox/"$grep_ff"/chrome"
path_to_ff_themes=""$HOME"/.mozilla/FoxThemes"
theme_name="userChrome.css"

    if [ -d "$path_to_ff" ]; then
        cp -rf "$path_to_ff_themes"/"$RICETHEME"/"$theme_name" "$path_to_ff"
    else
        echo "Somthing wrong"
    fi
}

# blender_conf() {
# 	scheme_path="$HOME/.config/blender/colorshemas/"$RICETHEME"/"
# 	if [ -f  $scheme_path/tealize.xml ]; then
# 		sed -i "s/gtk-theme-name=.*/gtk-theme-name="\"""$RICETHEME"""\"/g" "$HOME"/.config/blender/4.2/config/bookmarks.txt
# 	fi
# }

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q main-2 -c "${rice_dir}"/config.ini &
	done
}

launch_bars
set_gtk_theme
set_icons
set_cursor
set_network_manager
set_picom_config
set_launcher_config
set_firefox_theme