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
read -r RICETHEME < "$HOME"/.config/i3/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"

# Terminate already running bar instances
killall -q polybar
killall -q eww
# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

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
		-e "s/\".*:class_g = 'Alacritty'\"/\"100:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"100:class_g = 'FloaTerm'\"/g"
}

# Set dunst notification daemon config
set_dunst_config() {
	sed -i "$HOME"/.config/i3/dunstrc \
		-e "s/transparency = .*/transparency = 3/g" \
		-e "s/frame_color = .*/frame_color = \"#faf4ed\"/g" \
		-e "s/separator_color = .*/separator_color = \"#907aa9\"/g" \
		-e "s/font = .*/font = JetBrainsMono NF Medium 9/g" \
		-e "s/foreground='.*'/foreground='#575279'/g"

	sed -i '/urgency_low/Q' "$HOME"/.config/i3/dunstrc
	cat >>"$HOME"/.config/i3/dunstrc <<-_EOF_
		[urgency_low]
		timeout = 3
		background = "#faf4ed"
		foreground = "#51576d"

		[urgency_normal]
		timeout = 6
		background = "#faf4ed"
		foreground = "#51576d"

		[urgency_critical]
		timeout = 0
		background = "#faf4ed"
		foreground = "#51576d"
	_EOF_
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

# Set jgmenu colors for Aline
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #faf4ed/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #575279/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #f2e9e1/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #575279/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #907aa9/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#faf4ed;/' \
		-e 's/\(background-alt: \).*/\1#faf4edE0;/' \
		-e 's/\(foreground: \).*/\1#575279;/' \
		-e 's/\(selected: \).*/\1#d7827e;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#faf4ed;/' \
		-e '13s/\(background-alt: \).*/\1#f2e9e1;/' \
		-e '14s/\(foreground: \).*/\1#575279;/' \
		-e '15s/\(selected: \).*/\1#d7827e;/' \
		-e '16s/\(active: \).*/\1#286983;/' \
		-e '17s/\(urgent: \).*/\1#d7827e;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#faf4edE6;/' \
		-e 's/\(main-fg: \).*/\1#575279;/' \
		-e 's/\(select-bg: \).*/\1#d7827e;/' \
		-e 's/\(select-fg: \).*/\1#575279;/'
}

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q aline-bar -c "${rice_dir}"/config.ini &
	done

}

### ---------- Apply Configurations ---------- ###

set_term_config
set_picom_config
launch_bars
set_dunst_config
set_eww_colors
set_jgmenu_colors
set_launcher_config
