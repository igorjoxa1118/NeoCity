#!/usr/bin/env bash
#  ██╗  ██╗ █████╗ ██████╗ ██╗      █████╗     ██████╗ ██╗ ██████╗███████╗
#  ██║ ██╔╝██╔══██╗██╔══██╗██║     ██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  █████╔╝ ███████║██████╔╝██║     ███████║    ██████╔╝██║██║     █████╗
#  ██╔═██╗ ██╔══██║██╔══██╗██║     ██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ██║  ██╗██║  ██║██║  ██║███████╗██║  ██║    ██║  ██║██║╚██████╗███████╗
#  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
#  Author  :  z0mbi3
#  Url     :  https://github.com/gh0stzk/dotfiles
#  About   :  This file will configure and launch the rice.
#
read -r RICETHEME < "$HOME"/.config/i3/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_dir="$HOME/.config/i3"

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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Vallunar2.0-dark"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Vallunar2.0-dark/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Vallunar2.0-dark/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (Zombie-Night) Color scheme for Karla Rice

# Default colors
[colors.primary]
background = "#0b0e10"
foreground = "#afb1db"

# Cursor colors
[colors.cursor]
cursor = "#8656e3"
text = "#0b0b12"

# Normal colors
[colors.normal]
black = "#2d2b36"
blue = "#5884d4"
cyan = "#7df0f0"
green = "#61b33e"
magenta = "#7a44e3"
red = "#e7034a"
white = "#faf7ff"
yellow = "#ffb964"

# Bright colors
[colors.bright]
black = "#373542"
blue = "#5f90ea"
cyan = "#97f0f0"
green = "#6fb352"
magenta = "#8656e3"
red = "#e71c5b"
white = "#fdfcff"
yellow = "#ffb964"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = false; shadow = false; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#000000\"/g" \
		-e "s/corner-radius = .*/corner-radius = 0/g" \
		-e "s/\".*:class_g = 'Alacritty'\"/\"95:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"95:class_g = 'FloaTerm'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Karla rice
\$bg: #0b0e10;
\$bg-alt: #111517;
\$fg: #afb1db;
\$black: #373542;
\$lightblack: #262831;
\$red: #e7034a;
\$blue: #5884d4;
\$cyan: #7df0f0;
\$magenta: #7a44e3;
\$green: #61b33e;
\$yellow: #ffb964;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Karla
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #0b0e10/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #afb1db/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #111517/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #afb1db/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #373542/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#0b0e10F7;/' \
		-e 's/\(background-alt: \).*/\1#0b0e10F5;/' \
		-e 's/\(foreground: \).*/\1#afb1db;/' \
		-e 's/\(selected: \).*/\1#0a8ede;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#0b0e10F7;/' \
		-e '13s/\(background-alt: \).*/\1#0b0e10F5;/' \
		-e '14s/\(foreground: \).*/\1#afb1db;/' \
		-e '15s/\(selected: \).*/\1#5884d4;/' \
		-e '16s/\(active: \).*/\1#61b33e;/' \
		-e '17s/\(urgent: \).*/\1#e71c5b;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#0b0e10F7;/' \
		-e 's/\(main-fg: \).*/\1#afb1db;/' \
		-e 's/\(select-bg: \).*/\1#3d7fea;/' \
		-e 's/\(select-fg: \).*/\1#0b0e10;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
#HEIGHT=$((37 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		(MONITOR=$mon polybar -q karla-bar -c "${rice_dir}"/config.ini) &
	done

}

### ---------- Apply Configurations ---------- ###
set_gtk_theme
set_icons
set_firefox_theme

set_term_config
#set_picom_config
launch_bars
set_eww_colors
set_jgmenu_colors
set_launcher_config
