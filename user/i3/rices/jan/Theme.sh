#!/usr/bin/env bash
#       ██╗ █████╗ ███╗   ██╗    ██████╗ ██╗ ██████╗███████╗
#       ██║██╔══██╗████╗  ██║    ██╔══██╗██║██╔════╝██╔════╝
#       ██║███████║██╔██╗ ██║    ██████╔╝██║██║     █████╗
#  ██   ██║██╔══██║██║╚██╗██║    ██╔══██╗██║██║     ██╔══╝
#  ╚█████╔╝██║  ██║██║ ╚████║    ██║  ██║██║╚██████╗███████╗
#   ╚════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"besgnulinux-mono-cyan"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=besgnulinux-mono-cyan/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=besgnulinux-mono-cyan/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (CyberPunk) Color scheme for Jan Rice

# Default colors
[colors.primary]
background = "#212a4c"
foreground = "#27fbfe"

# Cursor colors
[colors.cursor]
cursor = "#fb007a"
text = "#212a4c"

# Normal colors
[colors.normal]
black = "#626483"
blue = "#19bffe"
cyan = "#43fbff"
green = "#a6e22e"
magenta = "#6800d2"
red = "#fb007a"
white = "#d9d9d9"
yellow = "#f3e430"

# Bright colors
[colors.bright]
black = "#626483"
blue = "#58AFC2"
cyan = "#926BCA"
green = "#a6e22e"
magenta = "#472575"
red = "#fb007a"
white = "#f1f1f1"
yellow = "#f3e430"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = true; shadow = false; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#000000\"/g" \
		-e "s/corner-radius = .*/corner-radius = 0/g" \
		-e "s/\".*:class_g = 'Xfce4-terminal'\"/\"80:class_g = 'Xfce4-terminal'\"/g" \
		-e "s/\".*:class_g = 'Deadbeef'\"/\"80:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g = 'XTerm'\"/\"80:class_g = 'XTerm'\"/g" \
		-e "s/\".*:class_g = 'kitty'\"/\"80:class_g = 'kitty'\"/g" \
		-e "s/\".*:class_g = 'TelegramDesktop'\"/\"80:class_g = 'TelegramDesktop'\"/g" \
		-e "s/\".*:class_g *= 'Thunar'\"/\"80:class_g = 'Thunar'\"/g" \
		-e "s/\".*:class_g *= 'Caja'\"/\"80:class_g = 'Caja'\"/g" \
		-e "s/\".*:class_g *= 'Rofi'\"/\"80:class_g = 'Rofi'\"/g" \
		-e "s/\".*:class_g *= 'Conky'\"/\"80:class_g = 'Deadbeef'\"/g" \
		-e "s/\".*:class_g *= 'Nm-applet'\"/\"80:class_g = 'Nm-applet'\"/g" \
		-e "s/\".*:class_g *= 'NetworkManager'\"/\"80:class_g = 'NetworkManager'\"/g" \
		-e "s/\".*:class_g *= 'qBittorrent'\"/\"80:class_g = 'qBittorrent'\"/g" \
		-e "s/\".*:class_g *= 'transmission-gtk'\"/\"80:class_g = 'transmission-gtk'\"/g" \
		-e "s/\".*:class_g *= 'Polybar'\"/\"80:class_g = 'Polybar'\"/g" \
		-e "s/\".*:class_g *= 'code-oss'\"/\"80:class_g = 'code-oss'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Jan rice
\$bg: #212a4c;
\$bg-alt: #09021f;
\$fg: #4DD0E1;
\$black: #626483;
\$lightblack: #262831;
\$red: #fb007a;
\$blue: #58AFC2;
\$cyan: #926BCA;
\$magenta: #583794;
\$green: #a6e22e;
\$yellow: #f3e430;
\$archicon: #0f94d2;
EOF
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/src/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"Terminess Nerd Font Mono Bold 10";/' \
		-e 's/\(background: \).*/\1#212a4cF0;/' \
		-e 's/\(background-alt: \).*/\1#212a4cE0;/' \
		-e 's/\(foreground: \).*/\1#4DD0E1;/' \
		-e 's/\(selected: \).*/\1#1b4967f0;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/src/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#212a4cF0;/' \
		-e '13s/\(background-alt: \).*/\1#212a4c;/' \
		-e '14s/\(foreground: \).*/\1#27fbfe;/' \
		-e '15s/\(selected: \).*/\1#19bffe;/' \
		-e '16s/\(active: \).*/\1#a6e22e;/' \
		-e '17s/\(urgent: \).*/\1#fb007a;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/src/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#212a4cF0;/' \
		-e 's/\(main-fg: \).*/\1#4DD0E1;/' \
		-e 's/\(select-bg: \).*/\1#fb007a;/' \
		-e 's/\(select-fg: \).*/\1#212a4c;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "${rice_dir}"/config.ini &
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
