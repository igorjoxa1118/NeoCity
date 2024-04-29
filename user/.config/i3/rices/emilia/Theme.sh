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

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

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

# Set dunst notification daemon config
set_dunst_config() {
	sed -i "$HOME"/.config/i3/dunstrc \
		-e "s/transparency = .*/transparency = 0/g" \
		-e "s/frame_color = .*/frame_color = \"#171924\"/g" \
		-e "s/separator_color = .*/separator_color = \"#7aa2f7\"/g" \
		-e "s/font = .*/font = JetBrainsMono NF Medium 9/g" \
		-e "s/foreground='.*'/foreground='#f9f9f9'/g"

	sed -i '/urgency_low/Q' "$HOME"/.config/i3/dunstrc
	cat >>"$HOME"/.config/i3/dunstrc <<-_EOF_
		[urgency_low]
		timeout = 3
		background = "#171924"
		foreground = "#7aa2f7"

		[urgency_normal]
		timeout = 6
		background = "#171924"
		foreground = "#7aa2f7"

		[urgency_critical]
		timeout = 0
		background = "#171924"
		foreground = "#7aa2f7"
	_EOF_
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
		-e 's/\(selected: \).*/\1#7aa2f7;/' \
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

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q emi-bar -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q emi-bar2 -c "${rice_dir}"/config.ini &
	done
}

### ---------- Apply Configurations ---------- ###

set_term_config
set_picom_config
launch_bars
set_eww_colors
set_jgmenu_colors
set_dunst_config
set_launcher_config
