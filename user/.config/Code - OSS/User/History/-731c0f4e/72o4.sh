#!/usr/bin/env bash
#  ███╗   ███╗ █████╗ ██████╗ ██╗███████╗ ██████╗ ██╗         ██████╗ ██╗ ██████╗███████╗
#  ████╗ ████║██╔══██╗██╔══██╗██║██╔════╝██╔═══██╗██║         ██╔══██╗██║██╔════╝██╔════╝
#  ██╔████╔██║███████║██████╔╝██║███████╗██║   ██║██║         ██████╔╝██║██║     █████╗
#  ██║╚██╔╝██║██╔══██║██╔══██╗██║╚════██║██║   ██║██║         ██╔══██╗██║██║     ██╔══╝
#  ██║ ╚═╝ ██║██║  ██║██║  ██║██║███████║╚██████╔╝███████╗    ██║  ██║██║╚██████╗███████╗
#  ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
# (Dracula) color scheme for Marisol Rice

# Default colors
[colors.primary]
background = "#4c566a"
foreground = "#f8f8f2"

# Cursor colors
[colors.cursor]
cursor = "#f8f8f2"
text = "#4c566a"

# Normal colors
[colors.normal]
black = "#21222c"
blue = "#bd93f9"
cyan = "#8be9fd"
green = "#50fa7b"
magenta = "#ff79c6"
red = "#ff5555"
white = "#f8f8f2"
yellow = "#f1fa8c"

# Bright colors
[colors.bright]
black = "#6272a4"
blue = "#d6acff"
cyan = "#a4ffff"
green = "#69ff94"
magenta = "#ff92df"
red = "#ff6e6e"
white = "#ffffff"
yellow = "#ffffa5"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = true; shadow = false; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#000000\"/g" \
		-e "s/corner-radius = .*/corner-radius = 0/g" \
		-e "s/\".*:class_g = 'Alacritty'\"/\"100:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"100:class_g = 'FloaTerm'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Marisol rice
\$bg: #4c566a;
\$bg-alt: #2f3240;
\$fg: #f8f8f2;
\$black: #21222c;
\$lightblack: #727169;
\$red: #ff5555;
\$blue: #bd93f9;
\$cyan: #8be9fd;
\$magenta: #ff79c6;
\$green: #50fa7b;
\$yellow: #f1fa8c;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Marisol
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #4c566a/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #f8f8f2/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #4c566a/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #f8f8f2/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #bd93f9/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#4c566a;/' \
		-e 's/\(background-alt: \).*/\1#4c566aE0;/' \
		-e 's/\(foreground: \).*/\1#f8f8f2;/' \
		-e 's/\(selected: \).*/\1#566a7f;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#4c566a;/' \
		-e '13s/\(background-alt: \).*/\1#2f3240;/' \
		-e '14s/\(foreground: \).*/\1#f8f8f2;/' \
		-e '15s/\(selected: \).*/\1#bd93f9;/' \
		-e '16s/\(active: \).*/\1#50fa7b;/' \
		-e '17s/\(urgent: \).*/\1#ff6e6e;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#4c566aE6;/' \
		-e 's/\(main-fg: \).*/\1#f8f8f2;/' \
		-e 's/\(select-bg: \).*/\1#bd93f9;/' \
		-e 's/\(select-fg: \).*/\1#f8f8f2;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q marisol -c "${rice_dir}"/config.ini &
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
