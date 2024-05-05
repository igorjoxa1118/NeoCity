#!/usr/bin/env bash
#  ██████╗ ██████╗ ███████╗███╗   ██╗██████╗  █████╗     ██████╗ ██╗ ██████╗███████╗
#  ██╔══██╗██╔══██╗██╔════╝████╗  ██║██╔══██╗██╔══██╗    ██╔══██╗██║██╔════╝██╔════╝
#  ██████╔╝██████╔╝█████╗  ██╔██╗ ██║██║  ██║███████║    ██████╔╝██║██║     █████╗
#  ██╔══██╗██╔══██╗██╔══╝  ██║╚██╗██║██║  ██║██╔══██║    ██╔══██╗██║██║     ██╔══╝
#  ██████╔╝██║  ██║███████╗██║ ╚████║██████╔╝██║  ██║    ██║  ██║██║╚██████╗███████╗
#  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝ ╚═════╝╚══════╝
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
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"buuf-nestort"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=buuf-nestort/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=buuf-nestort/g" "$HOME"/.config/gtk-4.0/settings.ini	
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
# (Everforest) color scheme for Brenda Rice

# Default colors
[colors.primary]
background = "#2d353b"
foreground = "#d3c6aa"

# Cursor colors
[colors.cursor]
cursor = "#d3c6aa"
text = "#2d353b"

# Normal colors
[colors.normal]
black   = "#475258"
red     = "#e67e80"
green   = "#a7c080"
yellow  = "#dbbc7f"
blue    = "#7fbbb3"
magenta = "#d699b6"
cyan    = "#83c092"
white   = "#d3c6aa"

# Bright colors
[colors.bright]
black   = "#475258"
red     = "#e67e80"
green   = "#a7c080"
yellow  = "#dbbc7f"
blue    = "#7fbbb3"
magenta = "#d699b6"
cyan    = "#83c092"
white   = "#d3c6aa"
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
		-e "s/frame_color = .*/frame_color = \"#2d353b\"/g" \
		-e "s/separator_color = .*/separator_color = \"#d3c6aa\"/g" \
		-e "s/font = .*/font = JetBrainsMono NF Medium 9/g" \
		-e "s/foreground='.*'/foreground='#7fbbb3'/g"

	sed -i '/urgency_low/Q' "$HOME"/.config/i3/dunstrc
	cat >>"$HOME"/.config/i3/dunstrc <<-_EOF_
		[urgency_low]
		timeout = 3
		background = "#2d353b"
		foreground = "#d3c6aa"

		[urgency_normal]
		timeout = 6
		background = "#2d353b"
		foreground = "#d3c6aa"

		[urgency_critical]
		timeout = 0
		background = "#2d353b"
		foreground = "#d3c6aa"
	_EOF_
}

# Set eww colors
set_eww_colors() {
	cat >"$HOME"/.config/i3/eww/colors.scss <<EOF
// Eww colors for Brenda rice
\$bg: #2d353b;
\$bg-alt: #272e33;
\$fg: #d3c6aa;
\$black: #475258;
\$lightblack: #262831;
\$red: #e67e80;
\$blue: #7fbbb3;
\$cyan: #83c092;
\$magenta: #d699b6;
\$green: #a7c080;
\$yellow: #dbbc7f;
\$archicon: #0f94d2;
EOF
}

# Set jgmenu colors for Brenda
set_jgmenu_colors() {
	sed -i "$HOME"/.config/i3/jgmenurc \
		-e 's/color_menu_bg = .*/color_menu_bg = #2d353b/' \
		-e 's/color_norm_fg = .*/color_norm_fg = #d3c6aa/' \
		-e 's/color_sel_bg = .*/color_sel_bg = #475258/' \
		-e 's/color_sel_fg = .*/color_sel_fg = #d3c6aa/' \
		-e 's/color_sep_fg = .*/color_sep_fg = #a7c080/'
}

# Set Rofi launcher config
set_launcher_config() {
	sed -i "$HOME/.config/i3/scripts/Launcher.rasi" \
		-e '22s/\(font: \).*/\1"JetBrainsMono NF Bold 9";/' \
		-e 's/\(background: \).*/\1#2d353b;/' \
		-e 's/\(background-alt: \).*/\1#2d353bE0;/' \
		-e 's/\(foreground: \).*/\1#d3c6aa;/' \
		-e 's/\(selected: \).*/\1#41484b;/' \
		-e "s/rices\/[[:alnum:]\-]*/rices\/${RICETHEME}/g"

	# NetworkManager launcher
	sed -i "$HOME/.config/i3/scripts/NetManagerDM.rasi" \
		-e '12s/\(background: \).*/\1#2d353b;/' \
		-e '13s/\(background-alt: \).*/\1#272e33;/' \
		-e '14s/\(foreground: \).*/\1#d3c6aa;/' \
		-e '15s/\(selected: \).*/\1#7fbbb3;/' \
		-e '16s/\(active: \).*/\1#a7c080;/' \
		-e '17s/\(urgent: \).*/\1#e67e80;/'

	# WallSelect menu colors
	sed -i "$HOME/.config/i3/scripts/WallSelect.rasi" \
		-e 's/\(main-bg: \).*/\1#2d353bE6;/' \
		-e 's/\(main-fg: \).*/\1#d3c6aa;/' \
		-e 's/\(select-bg: \).*/\1#475258;/' \
		-e 's/\(select-fg: \).*/\1#2d353b;/'
}

# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q brenda -c "${rice_dir}"/config.ini &
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
set_dunst_config
set_launcher_config
