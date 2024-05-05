#!/usr/bin/env bash
#  ██████╗  █████╗ ███╗   ██╗██╗███████╗██╗      █████╗     ██████╗ ██╗ ██████╗███████╗
#  ██╔══██╗██╔══██╗████╗  ██║██║██╔════╝██║     ██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  ██║  ██║███████║██╔██╗ ██║██║█████╗  ██║     ███████║    ██████╔╝██║██║     █████╗
#  ██║  ██║██╔══██║██║╚██╗██║██║██╔══╝  ██║     ██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ██████╔╝██║  ██║██║ ╚████║██║███████╗███████╗██║  ██║    ██║  ██║██║╚██████╗███████╗
#  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
# (Catppuccin Mocha) color scheme for Daniela Rice

# Default colors
[colors.primary]
background = "#181825"
foreground = "#CDD6F4"

# Cursor colors
[colors.cursor]
text = "#181825"
cursor = "#F5E0DC"

[colors.selection]
text = "#181825"
background = "#F5E0DC"

# Normal colors
[colors.normal]
black = "#45475A"
red = "#F38BA8"
green = "#A6E3A1"
yellow = "#F9E2AF"
blue = "#89B4FA"
magenta = "#F5C2E7"
cyan = "#94E2D5"
white = "#BAC2DE"

# Bright colors
[colors.bright]
black = "#585B70"
red = "#F38BA8"
green = "#A6E3A1"
yellow = "#F9E2AF"
blue = "#89B4FA"
magenta = "#F5C2E7"
cyan = "#94E2D5"
white = "#A6ADC8"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = true; shadow = true; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#181825\"/g" \
		-e "s/corner-radius = .*/corner-radius = 6/g" \
		-e "s/\".*:class_g = 'Alacritty'\"/\"100:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"100:class_g = 'FloaTerm'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Daniela rice
\$bg: #181825;
\$bg-alt: #1e1e2e;
\$fg: #CDD6F4;
\$black: #45475A;
\$lightblack: #262831;
\$red: #F38BA8;
\$blue: #89B4FA;
\$cyan: #94E2D5;
\$magenta: #F5C2E7;
\$green: #A6E3A1;
\$yellow: #F9E2AF;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Daniela
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #181825/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #CDD6F4/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #1e1e2e/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #CDD6F4/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #45475A/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#181825;/' \
		-e 's/\(background-alt: \).*/\1#181825E0;/' \
		-e 's/\(foreground: \).*/\1#CDD6F4;/' \
		-e 's/\(selected: \).*/\1#3c4c3f;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#181825;/' \
		-e '13s/\(background-alt: \).*/\1#1e1e2e;/' \
		-e '14s/\(foreground: \).*/\1#CDD6F4;/' \
		-e '15s/\(selected: \).*/\1#89B4FA;/' \
		-e '16s/\(active: \).*/\1#A6E3A1;/' \
		-e '17s/\(urgent: \).*/\1#F38BA8;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#181825E6;/' \
		-e 's/\(main-fg: \).*/\1#CDD6F4;/' \
		-e 's/\(select-bg: \).*/\1#F5C2E7;/' \
		-e 's/\(select-fg: \).*/\1#181825;/'
}

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q dani -c "${rice_dir}"/config.ini &
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
