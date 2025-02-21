#!/usr/bin/env bash
#  ███████╗██╗██╗    ██╗   ██╗██╗ █████╗     ██████╗ ██╗ ██████╗███████╗
#  ██╔════╝██║██║    ██║   ██║██║██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  ███████╗██║██║    ██║   ██║██║███████║    ██████╔╝██║██║     █████╗
#  ╚════██║██║██║    ╚██╗ ██╔╝██║██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ███████║██║███████╗╚████╔╝ ██║██║  ██║    ██║  ██║██║╚██████╗███████╗
#  ╚══════╝╚═╝╚══════╝ ╚═══╝  ╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"BeautySolar"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=BeautySolar/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=BeautySolar/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (Gruvbox) Color scheme for Silvia Rice

# Default colors
[colors.primary]
background = "#3c3836"
foreground = "#fbf1c7"

# Cursor colors
[colors.cursor]
cursor = "#fbf1c7"
text = "#3c3836"

# Normal colors
[colors.normal]
black = "#a89984"
blue = "#458588"
cyan = "#689d6a"
green = "#98971a"
magenta = "#b16286"
red = "#cc241d"
white = "#ebdbb2"
yellow = "#d79921"

# Bright colors
[colors.bright]
black = "#a89984"
blue = "#83a598"
cyan = "#8ec07c"
green = "#b8bb26"
magenta = "#d3869b"
red = "#fb4934"
white = "#ebdbb2"
yellow = "#fabd2f"
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
// Eww colors for Silvia rice
\$bg: #3c3836;
\$bg-alt: #2E2E2E;
\$fg: #fbf1c7;
\$black: #a89984;
\$lightblack: #262831;
\$red: #fb4934;
\$blue: #83a598;
\$cyan: #8ec07c;
\$magenta: #d3869b;
\$green: #b8bb26;
\$yellow: #fabd2f;
\$archicon: #0f94d2;
EOF
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/src/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"scientifica 12";/' \
		-e 's/\(background: \).*/\1#3c3836;/' \
		-e 's/\(background-alt: \).*/\1#3c3836E0;/' \
		-e 's/\(foreground: \).*/\1#fbf1c7;/' \
		-e 's/\(selected: \).*/\1#7c5c20;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/src/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#3c3836;/' \
		-e '13s/\(background-alt: \).*/\1#2E2E2E;/' \
		-e '14s/\(foreground: \).*/\1#fbf1c7;/' \
		-e '15s/\(selected: \).*/\1#d79921;/' \
		-e '16s/\(active: \).*/\1#689d6a;/' \
		-e '17s/\(urgent: \).*/\1#fb4934;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/src/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#3c3836E6;/' \
		-e 's/\(main-fg: \).*/\1#fbf1c7;/' \
		-e 's/\(select-bg: \).*/\1#d79921;/' \
		-e 's/\(select-fg: \).*/\1#3c3836;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q cata-bar -c "${rice_dir}"/config.ini &
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
