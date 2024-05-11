#!/usr/bin/env bash
#  ██╗███████╗ █████╗ ██████╗ ███████╗██╗         ██████╗ ██╗ ██████╗███████╗
#  ██║██╔════╝██╔══██╗██╔══██╗██╔════╝██║         ██╔══██╗██║██╔════╝██╔════╝
#  ██║███████╗███████║██████╔╝█████╗  ██║         ██████╔╝██║██║     █████╗
#  ██║╚════██║██╔══██║██╔══██╗██╔══╝  ██║         ██╔══██╗██║██║     ██╔══╝
#  ██║███████║██║  ██║██████╔╝███████╗███████╗    ██║  ██║██║╚██████╗███████╗
#  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"Flat-Remix-Blue-Dark"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Flat-Remix-Blue-Dark/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Flat-Remix-Blue-Dark/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (Onedark) Color scheme for Isabel Rice

# Default colors
[colors.primary]
background = "#14171c"
foreground = "#abb2bf"

# Cursor colors
[colors.cursor]
cursor = "#abb2bf"
text = "#14171c"

# Normal colors
[colors.normal]
black = "#1e2127"
blue = "#4889be"
cyan = "#49919a"
green = "#81ae5f"
magenta = "#7560d3"
red = "#be5046"
white = "#abb2bf"
yellow = "#d19a66"

# Bright colors
[colors.bright]
black = "#5c6370"
blue = "#61afef"
cyan = "#56b6c2"
green = "#98c379"
magenta = "#8677cf"
red = "#e06c75"
white = "#ffffff"
yellow = "#e5c07b"
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
// Eww colors for Isabel rice
\$bg: #14171c;
\$bg-alt: #181b21;
\$fg: #b8bfe5;
\$black: #5c6370;
\$lightblack: #262831;
\$red: #be5046;
\$blue: #4889be;
\$cyan: #49919a;
\$magenta: #7560d3;
\$green: #81ae5f;
\$yellow: #d19a66;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Isabel
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #14171c/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #b8bfe5/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #181b21/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #b8bfe5/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #5c6370/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"Terminess Nerd Font Mono Bold 10";/' \
		-e 's/\(background: \).*/\1#14171c;/' \
		-e 's/\(background-alt: \).*/\1#14171cE0;/' \
		-e 's/\(foreground: \).*/\1#b8bfe5;/' \
		-e 's/\(selected: \).*/\1#524688;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#14171c;/' \
		-e '13s/\(background-alt: \).*/\1#181b21;/' \
		-e '14s/\(foreground: \).*/\1#b8bfe5;/' \
		-e '15s/\(selected: \).*/\1#8677cf;/' \
		-e '16s/\(active: \).*/\1#81ae5f;/' \
		-e '17s/\(urgent: \).*/\1#e06c75;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#14171cE6;/' \
		-e 's/\(main-fg: \).*/\1#b8bfe5;/' \
		-e 's/\(select-bg: \).*/\1#8677cf;/' \
		-e 's/\(select-fg: \).*/\1#14171c;/'
}

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q isa-bar -c "${rice_dir}"/config.ini &
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
