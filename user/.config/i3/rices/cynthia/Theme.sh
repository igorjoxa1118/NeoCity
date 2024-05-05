#!/usr/bin/env bash
#   ██████╗██╗   ██╗███╗   ██╗████████╗██╗  ██╗██╗ █████╗     ██████╗ ██╗ ██████╗███████╗
#  ██╔════╝╚██╗ ██╔╝████╗  ██║╚══██╔══╝██║  ██║██║██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  ██║      ╚████╔╝ ██╔██╗ ██║   ██║   ███████║██║███████║    ██████╔╝██║██║     █████╗
#  ██║       ╚██╔╝  ██║╚██╗██║   ██║   ██╔══██║██║██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ╚██████╗   ██║   ██║ ╚████║   ██║   ██║  ██║██║██║  ██║    ██║  ██║██║╚██████╗███████╗
#   ╚═════╝   ╚═╝   ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
#  Author  :  z0mbi3
#  Url     :  https://github.com/gh0stzk/dotfiles
#  About   :  This file will configure and launch the rice.
#

# Set i3 configuration for Cynthia
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Gruvbox"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Gruvbox/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Gruvbox/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (Kanagawa Dragon) Color scheme for Cynthia Rice

# Default colors
[colors.primary]
background = '#181616'
foreground = '#c5c9c5'

# Cursor colors
[colors.cursor]
cursor = "#8a9a7b"
text = "#181616"

# Normal colors
[colors.normal]
black = '#0d0c0c'
blue = '#8ba4b0'
cyan = '#8ea4a2'
green = '#8a9a7b'
magenta = '#a292a3'
red = '#c4746e'
white = '#C8C093'
yellow = '#c4b28a'

# Bright colors
[colors.bright]
black = '#a6a69c'
blue = '#7FB4CA'
cyan = '#7AA89F'
green = '#87a987'
magenta = '#938AA9'
red = '#E46876'
white = '#c5c9c5'
yellow = '#E6C384'
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
// Eww colors for Cynthia rice
\$bg: #181616;
\$bg-alt: #1c1a1a;
\$fg: #c5c9c5;
\$black: #a6a69c;
\$lightblack: #262831;
\$red: #c4746e;
\$blue: #8ba4b0;
\$cyan: #8ea4a2;
\$magenta: #a292a3;
\$green: #8a9a7b;
\$yellow: #c4b28a;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Cynthia
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #181616/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #c5c9c5/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #8a9a7b/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #181616/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #8a9a7b/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"Terminess Nerd Font Mono Bold 10";/' \
		-e 's/\(background: \).*/\1#181616;/' \
		-e 's/\(background-alt: \).*/\1#181616E0;/' \
		-e 's/\(foreground: \).*/\1#c5c9c5;/' \
		-e 's/\(selected: \).*/\1#7f7051;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#181616;/' \
		-e '13s/\(background-alt: \).*/\1#1c1a1a;/' \
		-e '14s/\(foreground: \).*/\1#c5c9c5;/' \
		-e '15s/\(selected: \).*/\1#8ba4b0;/' \
		-e '16s/\(active: \).*/\1#8a9a7b;/' \
		-e '17s/\(urgent: \).*/\1#c4746e;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#181616E6;/' \
		-e 's/\(main-fg: \).*/\1#c5c9c5;/' \
		-e 's/\(select-bg: \).*/\1#8ea4a2;/' \
		-e 's/\(select-fg: \).*/\1#181616;/'
}

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		(MONITOR=$mon polybar -q cyn-bar -c "${rice_dir}"/config.ini) &
		(MONITOR=$mon polybar -q cyn-bar2 -c "${rice_dir}"/config.ini) &
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
