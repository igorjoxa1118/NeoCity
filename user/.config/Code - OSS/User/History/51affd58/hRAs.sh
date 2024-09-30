#!/usr/bin/env bash
#  ███████╗███╗   ███╗██╗██╗     ██╗ █████╗     ██████╗ ██╗ ██████╗███████╗
#  ██╔════╝████╗ ████║██║██║     ██║██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  █████╗  ██╔████╔██║██║██║     ██║███████║    ██████╔╝██║██║     █████╗
#  ██╔══╝  ██║╚██╔╝██║██║██║     ██║██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ███████╗██║ ╚═╝ ██║██║███████╗██║██║  ██║    ██║  ██║██║╚██████╗███████╗
#  ╚══════╝╚═╝     ╚═╝╚═╝╚══════╝╚═╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
# (Tokyo Night) color scheme for Emilia Rice

# Default colors
[colors.primary]
background = "#171924"
foreground = "#7aa2f7"

# Cursor colors
[colors.cursor]
cursor = "#7aa2f7"
text = "#171924"

# Normal colors
[colors.normal]
black = "#15161e"
blue = "#7aa2f7"
cyan = "#7dcfff"
green = "#9ece6a"
magenta = "#bb9af7"
red = "#f7768e"
white = "#a9b1d6"
yellow = "#e0af68"

# Bright colors
[colors.bright]
black = "#414868"
blue = "#7aa2f7"
cyan = "#7dcfff"
green = "#9ece6a"
magenta = "#bb9af7"
red = "#f7768e"
white = "#7aa2f7"
yellow = "#e0af68"
EOF
}

# Set compositor configuration
set_picom_config() {
	sed -i "$HOME"/.config/i3/picom.conf \
		-e "s/normal = .*/normal =  { fade = true; shadow = true; }/g" \
		-e "s/shadow-color = .*/shadow-color = \"#000000\"/g" \
		-e "s/corner-radius = .*/corner-radius = 6/g" \
		-e "s/\".*:class_g = 'Alacritty'\"/\"100:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"100:class_g = 'FloaTerm'\"/g"
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Emilia rice
\$bg: #171924;
\$bg-alt: #222330;
\$fg: #7aa2f7;
\$black: #414868;
\$lightblack: #262831;
\$red: #f7768e;
\$blue: #7aa2f7;
\$cyan: #7dcfff;
\$magenta: #bb9af7;
\$green: #9ece6a;
\$yellow: #e0af68;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Emilia
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #171924/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #7aa2f7/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #222330/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #7aa2f7/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #414868/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#171924;/' \
		-e 's/\(background-alt: \).*/\1#171924E0;/' \
		-e 's/\(foreground: \).*/\1#7aa2f7;/' \
		-e 's/\(selected: \).*/\1#333f5e;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#171924;/' \
		-e '13s/\(background-alt: \).*/\1#222330;/' \
		-e '14s/\(foreground: \).*/\1#7aa2f7;/' \
		-e '15s/\(selected: \).*/\1#7aa2f7;/' \
		-e '16s/\(active: \).*/\1#9ece6a;/' \
		-e '17s/\(urgent: \).*/\1#f7768e;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#171924E6;/' \
		-e 's/\(main-fg: \).*/\1#7aa2f7;/' \
		-e 's/\(select-bg: \).*/\1#7aa2f7;/' \
		-e 's/\(select-fg: \).*/\1#171924;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
HEIGHT=$((20 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar emi-bar -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar emi-bar2 -c "${rice_dir}"/config.ini &
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
