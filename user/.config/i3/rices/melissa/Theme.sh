#!/usr/bin/env bash
#  ███╗   ███╗███████╗██╗     ██╗███████╗███████╗ █████╗     ██████╗ ██╗ ██████╗███████╗
#  ████╗ ████║██╔════╝██║     ██║██╔════╝██╔════╝██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  ██╔████╔██║█████╗  ██║     ██║███████╗███████╗███████║    ██████╔╝██║██║     █████╗
#  ██║╚██╔╝██║██╔══╝  ██║     ██║╚════██║╚════██║██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ██║ ╚═╝ ██║███████╗███████╗██║███████║███████║██║  ██║    ██║  ██║██║╚██████╗███████╗
#  ╚═╝     ╚═╝╚══════╝╚══════╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Zafiro-Nord-Black-Blue"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Zafiro-Nord-Black-Blue/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Zafiro-Nord-Black-Blue/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (Nord) Color scheme for Melissa Rice

# Default colors
[colors.primary]
background = "#3b4252"
foreground = "#d8dee9"

# Cursor colors
[colors.cursor]
cursor = "#81a1c1"
text = "#3b4252"

# Normal colors
[colors.normal]
black = "#3b4252"
blue = "#81a1c1"
cyan = "#5e697d"
green = "#a3be8c"
magenta = "#b48ead"
red = "#bf616a"
white = "#e5e9f0"
yellow = "#ebcb8b"

# Bright colors
[colors.bright]
black = "#4c566a"
blue = "#81a1c1"
cyan = "#8fbcbb"
green = "#a3be8c"
magenta = "#b48ead"
red = "#bf616a"
white = "#eceff4"
yellow = "#ebcb8b"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = true; shadow = true; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#000000\"/g" \
		-e "s/corner-radius = .*/corner-radius = 6/g" \
		-e "s/\".*:class_g = 'Alacritty'\"/\"99:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"99:class_g = 'FloaTerm'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Melissa rice
\$bg: #3b4252;
\$bg-alt: #353C4A;
\$fg: #d8dee9;
\$black: #4c566a;
\$lightblack: #262831;
\$red: #bf616a;
\$blue: #81a1c1;
\$cyan: #5e697d;
\$magenta: #b48ead;
\$green: #a3be8c;
\$yellow: #ebcb8b;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Melissa
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #3b4252/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #d8dee9/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #353C4A/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #d8dee9/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #4c566a/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"Terminess Nerd Font Mono Bold 10";/' \
		-e 's/\(background: \).*/\1#3b4252;/' \
		-e 's/\(background-alt: \).*/\1#3b4252E0;/' \
		-e 's/\(foreground: \).*/\1#e5e9f0;/' \
		-e 's/\(selected: \).*/\1#5e697d;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#3b4252;/' \
		-e '13s/\(background-alt: \).*/\1#353C4A;/' \
		-e '14s/\(foreground: \).*/\1#e5e9f0;/' \
		-e '15s/\(selected: \).*/\1#5e697d;/' \
		-e '16s/\(active: \).*/\1#a3be8c;/' \
		-e '17s/\(urgent: \).*/\1#bf616a;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#3b4252E6;/' \
		-e 's/\(main-fg: \).*/\1#e5e9f0;/' \
		-e 's/\(select-bg: \).*/\1#5e697d;/' \
		-e 's/\(select-fg: \).*/\1#3b4252;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		(MONITOR=$mon polybar -q mel-bar -c "${rice_dir}"/config.ini) &
		(MONITOR=$mon polybar -q mel2-bar -c "${rice_dir}"/config.ini) &
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
set_jgmenu_colors
set_launcher_config
