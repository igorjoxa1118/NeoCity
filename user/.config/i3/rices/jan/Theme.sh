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
# (CyberPunk) Color scheme for Jan Rice

# Default colors
[colors.primary]
background = "#070219"
foreground = "#27fbfe"

# Cursor colors
[colors.cursor]
cursor = "#fb007a"
text = "#070219"

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
		-e "s/\".*:class_g = 'Alacritty'\"/\"96:class_g = 'Alacritty'\"/g" \
		-e "s/\".*:class_g = 'FloaTerm'\"/\"96:class_g = 'FloaTerm'\"/g"
}

# Set dunst notification daemon config
set_dunst_config() {
	sed -i "$HOME"/.config/i3/dunstrc \
		-e "s/transparency = .*/transparency = 8/g" \
		-e "s/frame_color = .*/frame_color = \"#070219\"/g" \
		-e "s/separator_color = .*/separator_color = \"#fb007a\"/g" \
		-e "s/font = .*/font = JetBrainsMono NF Medium 9/g" \
		-e "s/foreground='.*'/foreground='#27fbfe'/g"

	sed -i '/urgency_low/Q' "$HOME"/.config/i3/dunstrc
	cat >>"$HOME"/.config/i3/dunstrc <<-_EOF_
		[urgency_low]
		timeout = 3
		background = "#070219"
		foreground = "#27fbfe"

		[urgency_normal]
		timeout = 6
		background = "#070219"
		foreground = "#27fbfe"

		[urgency_critical]
		timeout = 0
		background = "#070219"
		foreground = "#27fbfe"
	_EOF_
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Jan rice
\$bg: #070219;
\$bg-alt: #09021f;
\$fg: #c0caf5;
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

# Set jgmenu colors for Jan
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #070219/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #c0caf5/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #09021f/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #c0caf5/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #626483/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"Terminess Nerd Font Mono Bold 10";/' \
		-e 's/\(background: \).*/\1#070219F0;/' \
		-e 's/\(background-alt: \).*/\1#070219E0;/' \
		-e 's/\(foreground: \).*/\1#c0caf5;/' \
		-e 's/\(selected: \).*/\1#fb007af0;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#070219F0;/' \
		-e '13s/\(background-alt: \).*/\1#070219;/' \
		-e '14s/\(foreground: \).*/\1#27fbfe;/' \
		-e '15s/\(selected: \).*/\1#19bffe;/' \
		-e '16s/\(active: \).*/\1#a6e22e;/' \
		-e '17s/\(urgent: \).*/\1#fb007a;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#070219F0;/' \
		-e 's/\(main-fg: \).*/\1#c0caf5;/' \
		-e 's/\(select-bg: \).*/\1#fb007a;/' \
		-e 's/\(select-fg: \).*/\1#070219;/'
}

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "${rice_dir}"/config.ini &
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
