#############################
#		Emilia Theme		#
#############################

# (Catppuccin Mocha colorscheme
 rosewater="#f5e0dc"
 flamingo="#f2cdcd"
 pink="#f5c2e7"
 mauve="#cba6f7"
 red="#f38ba8"
 maroon="#eba0ac"
 peach="#fab387"
 yellow="#f9e2af"
 green="#a6e3a1"
 teal="#94e2d5"
 sky="#89dceb"
 sapphire="#74c7ec"
 blue="#89b4fa"
 lavender="#b4befe"
 text="#cdd6f4"
 subtext1="#bac2de"
 subtext0="#a6adc8"
 overlay2="#9399b2"
 overlay1="#7f849c"
 overlay0="#6c7086"
 surface2="#585b70"
 surface1="#45475a"
 surface0="#313244"
 base="#1e1e2e"
 mantle="#181825"
 crust="#11111b"
 transparent="#FF00000"

# Bspwm options
BORDER_WIDTH="0"		# Bspwm border
NORMAL_BC="#414868"		# Normal border color
FOCUSED_BC="#bb9af7"	# Focused border color

# Terminal font & size
term_font_size="10"
term_font_name="MesloLGS NF Regular"

# Picom options
P_FADE="true"			# Fade true|false
P_SHADOWS="true"		# Shadows true|false
SHADOW_C="#cba6f7"		# Shadow color
P_CORNER_R="6"			# Corner radius (0 = disabled)
P_BLUR="false"			# Blur true|false
P_ANIMATIONS="@"		# (@ = enable) (# = disable)
P_TERM_OPACITY="1.0"	# Terminal transparency. Range: 0.1 - 1.0 (1.0 = disabled)

# Dunst
dunst_offset='(20, 60)'
dunst_origin='top-right'
dunst_transparency='0'
dunst_corner_radius='6'
dunst_font='MesloLGS NF Regular 9'
dunst_border='0'

# Gtk theme vars
gtk_theme="TokyoNight-zk"
gtk_icons="TokyoNight-SE"
gtk_cursor="Qogirr-Dark"
geany_theme="z0mbi3-TokyoNight"

# Wallpaper engine
# Available engines:
# - Theme	(Set a random wallpaper from rice directory)
# - CustomDir	(Set a random wallpaper from the directory you specified)
# - CustomImage	(Sets a specific image as wallpaper)
# - CustomAnimated (Set an animated wallpaper. "mp4, mkv, gif")
ENGINE="Theme"
CUSTOM_DIR="/path/to/dir"
CUSTOM_WALL="/path/to/image"
CUSTOM_ANIMATED="$HOME/.config/bspwm/src/assets/animated_wall.mp4"
