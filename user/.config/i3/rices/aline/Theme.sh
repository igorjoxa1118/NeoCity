#!/usr/bin/env bash
#   █████╗ ██╗     ██╗███╗   ██╗███████╗    ██████╗ ██╗ ██████╗███████╗
#  ██╔══██╗██║     ██║████╗  ██║██╔════╝    ██╔══██╗██║██╔════╝██╔════╝
#  ███████║██║     ██║██╔██╗ ██║█████╗      ██████╔╝██║██║     █████╗
#  ██╔══██║██║     ██║██║╚██╗██║██╔══╝      ██╔══██╗██║██║     ██╔══╝
#  ██║  ██║███████╗██║██║ ╚████║███████╗    ██║  ██║██║╚██████╗███████╗
#  ╚═╝  ╚═╝╚══════╝╚═╝╚═╝  ╚═══╝╚══════╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
#  Author  :  z0mbi3
#  Url     :  https://github.com/gh0stzk/dotfiles
#  About   :  This file will configure and launch the rice.
#
read -r RICETHEME < "$HOME"/.config/i3/config.d/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_dir="$HOME/.config/i3/config.d"

# Terminate already running bar instances
killall -q polybar
killall -q eww
# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

###--Start rice

set_gtk_theme() {
	sed -i "s/gtk-theme-name=.*/gtk-theme-name="$RICETHEME"/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-theme-name=.*/gtk-theme-name="$RICETHEME"/g" "$HOME"/.config/gtk-4.0/settings.ini
    sed -i "s/gtk-theme-name=.*/gtk-theme-name="\"""$RICETHEME"""\"/g" "$HOME"/.gtkrc-2.0
}

set_icons() {
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Magna-Dark-Icons"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Magna-Dark-Icons/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Magna-Dark-Icons/g" "$HOME"/.config/gtk-4.0/settings.ini	
}

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

# Reload terminal colors
set_term_config() {
	cat >"$HOME"/.config/alacritty/rice-colors.toml <<EOF
# (Rose Pine Dawn) color scheme for Aline Rice

# Default colors
[colors.primary]
background = "#faf4ed"
foreground = "#575279"

# Cursor colors
[colors.cursor]
text = "#575279"
cursor = "#cecacd"

# Normal colors
[colors.normal]
black = "#f2e9e1"
red = "#b4637a"
green = "#286983"
yellow = "#ea9d34"
blue = "#56949f"
magenta = "#907aa9"
cyan = "#d7827e"
white = "#575279"

# Bright colors
[colors.bright]
black = "#9893a5"
red = "#b4637a"
green = "#286983"
yellow = "#ea9d34"
blue = "#56949f"
magenta = "#907aa9"
cyan = "#d7827e"
white = "#575279"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = true; shadow = true; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#000000\"/g" \
		-e "s/corner-radius = .*/corner-radius = 6/g" \
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
		-e "s/\".*:class_g *= 'code-oss'\"/\"100:class_g = 'code-oss'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Aline rice
\$bg: #faf4ed;
\$bg-alt: #f2e9e1;
\$fg: #575279;
\$black: #9893a5;
\$lightblack: #262831;
\$red: #b4637a;
\$blue: #56949f;
\$cyan: #d7827e;
\$magenta: #907aa9;
\$green: #286983;
\$yellow: #ea9d34;
\$archicon: #0f94d2;
EOF
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/src/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#faf4ed;/' \
		-e 's/\(background-alt: \).*/\1#faf4edE0;/' \
		-e 's/\(foreground: \).*/\1#575279;/' \
		-e 's/\(selected: \).*/\1#666183;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/src/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#faf4ed;/' \
		-e '13s/\(background-alt: \).*/\1#f2e9e1;/' \
		-e '14s/\(foreground: \).*/\1#575279;/' \
		-e '15s/\(selected: \).*/\1#d7827e;/' \
		-e '16s/\(active: \).*/\1#286983;/' \
		-e '17s/\(urgent: \).*/\1#d7827e;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/src/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#faf4edE6;/' \
		-e 's/\(main-fg: \).*/\1#575279;/' \
		-e 's/\(select-bg: \).*/\1#d7827e;/' \
		-e 's/\(select-fg: \).*/\1#575279;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q aline-bar -c "${rice_dir}"/config.ini &
	done

}

### ---------- Apply Configurations ---------- ###
set_gtk_theme
set_icons
set_firefox_theme
set_term_config
set_picom_config
launch_bars
set_eww_colors
set_launcher_config
