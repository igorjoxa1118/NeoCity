#!/usr/bin/env bash

## Catppuccin mocha

read -r RICETHEME < "$HOME"/.config/i3/config.d/.rice
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_configd="$HOME/.config/i3/config.d"
i3_scr="$HOME/.config/i3/src"

# Terminate already running bar instances
killall -q polybar
killall -q eww

###--Start rice
rofi_launcher_color() {
	if [ -f "$HOME/.config/i3/src/launchers/type-3/shared/colors.rasi" ]; then
	 echo '' >  "$HOME/.config/i3/src/launchers/type-3/shared/colors.rasi"
	 cat "$HOME/.config/i3/rices/$RICETHEME/rofi/shared/colors.rasi" > "$HOME/.config/i3/src/launchers/type-3/shared/colors.rasi"
	fi
}
rofi_launcher_color

rofi_powermenu() {
# Удаляем старый блок кода, начиная с "/*****----- Global Properties -----*****/" и заканчивая "}"
sed -i '/\/\*\*\*\*----- Global Properties -----\*\*\*\*\//,/}/d' $HOME/.config/i3/src/powermenu/type-4/style-5.rasi

# Вставляем новый блок кода на место удалённого
cat << 'EOF' >> $HOME/.config/i3/src/powermenu/type-4/style-5.rasi
/*****----- Global Properties -----*****/
* {
    /* Resolution : 1920x1080 */
    mainbox-spacing:             52px;
    mainbox-margin:              0px 470px;
    message-margin:              0px 350px;
    message-padding:             15px;
    message-border-radius:       100%;
    listview-spacing:            25px;
    element-padding:             20px 40px 45px 40px;
    element-border-radius:       100%;

    prompt-font:                 "MesloLGS NF Regular Bold 32";
    textbox-font:                "MesloLGS NF Regular 10";
    element-text-font:           "feather Bold 48";

    /* Gradients */
    gradient-1:                  linear-gradient(45, #89b4fa, #a6da95);
    gradient-2:                  linear-gradient(0, #eba0ac, #7A72EC);
    gradient-3:                  linear-gradient(70, #f9e2af, #eba0ac);
    gradient-4:                  linear-gradient(135, #74c7ec, #89b4fa);
    gradient-5:                  linear-gradient(to left, #bdc3c7, #2c3e50);
    gradient-6:                  linear-gradient(to right, #1e1e2e, #1e1e2e, #1e1e2e);
    gradient-7:                  linear-gradient(to top, #74c7ec, #cba6f7, #eba0ac);
    gradient-8:                  linear-gradient(to bottom, #f38ba8, #493240);
    gradient-9:                  linear-gradient(0, #1a2a6c, #eba0ac, #f9e2af);
    gradient-10:                 linear-gradient(0, #283c86, #a6da95);
    gradient-11:                 linear-gradient(0, #89b4fa, #79CBCA, #E684AE);
    gradient-12:                 linear-gradient(0, #ff6e7f, #bfe9ff);
    gradient-13:                 linear-gradient(0, #f38ba8, #eba0ac);
    gradient-14:                 linear-gradient(0, #cba6f7, #cba6f7);
    gradient-15:                 linear-gradient(0, #a6da95, #a6da95);
    gradient-16:                 linear-gradient(0, #232526, #414345);
    gradient-17:                 linear-gradient(0, #833ab4, #eba0ac, #f9e2af);
    gradient-18:                 linear-gradient(0, #89b4fa, #74c7ec, #74c7ec, #89b4fa);
    gradient-19:                 linear-gradient(0, #03001e, #cba6f7, #ec38bc, #fdeff9);
    gradient-20:                 linear-gradient(0, #eba0ac, #061161);
    
    green:        #a6da95;
    bords:        #cba6f7;
    
    background-window:           var(gradient-6);
    background-normal:           #1e1e2e;
    background-selected:         #89b4fa;
    foreground-normal:           #cdd6f4;
    foreground-selected:         #1e1e2e;
}
EOF
}
rofi_powermenu

rofi_calendar_color() {
	if [ -f "$i3_scr/rofi-calendar/themes/colors.rasi" ]; then
	 echo '' >  "$i3_scr/rofi-calendar/themes/colors.rasi"
	 cat "$HOME/.config/i3/src/rofi-themes/colors/$RICETHEME.rasi" > "$i3_scr/rofi-calendar/themes/colors.rasi"
	fi
}
rofi_calendar_color

# Функция для применения тем GTK3 "на лету" через xsettingsd
set_gtk_theme() {
    # Создаем временный файл конфигурации для xsettingsd
    XSETTINGS_CONF="$HOME/.xsettingsd"
    cat <<EOF > "$XSETTINGS_CONF"
Net/ThemeName "$RICETHEME"
Net/IconThemeName "TokyoNight-SE"
Gtk/CursorThemeName "catppuccin-mocha-mauve-cursors"
EOF

    # Перезапускаем xsettingsd для применения изменений
    if pgrep -x "xsettingsd" > /dev/null; then
        killall xsettingsd
    fi
    xsettingsd &
}
set_gtk_theme

set_icons() {
    # Изменение иконок в конфигурационных файлах
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name="\"TokyoNight-SE"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=TokyoNight-SE/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=TokyoNight-SE/g" "$HOME"/.config/gtk-4.0/settings.ini
}
set_icons

set_cursor() {
    # Изменение курсоров в конфигурационных файлах
    sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name="\"catppuccin-mocha-mauve-cursors"\"/g" "$HOME"/.gtkrc-2.0
    sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-mauve-cursors/g" "$HOME"/.config/gtk-3.0/settings.ini
    sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-mauve-cursors/g" "$HOME"/.config/gtk-4.0/settings.ini
}
set_cursor

# NetworkManager launcher
set_network_manager() {
	sed -i 's|@import "colors/catppuccin-[^"]*"|@import "colors/catppuccin-mocha.rasi"|g' "$HOME/.config/i3/src/rofi-themes/NetManagerDM.rasi"
}
set_network_manager

# Reload terminal colors
set_term_config() {
	AL_CONFIG_DIR="$HOME/.config/alacritty"
	AL_RICE_DIR="$HOME/.config/i3/rices/$RICETHEME/alacritty"
		if [ -f $AL_CONFIG_DIR/alacritty.toml ]; then
			rm -rf $AL_CONFIG_DIR/*
			cp -rf $AL_RICE_DIR/* $AL_CONFIG_DIR
		fi
	KI_CONFIG_DIR="$HOME/.config/kitty"
	KI_RICE_DIR="$HOME/.config/i3/rices/$RICETHEME/kitty"
		if [ -f $KI_CONFIG_DIR/kitty.conf ]; then
			cp -rf $KI_RICE_DIR/kitty.conf $KI_CONFIG_DIR
		else
			cp -rf $HOME/.config/i3/rices/$RICETHEME/kitty/kitty.conf $HOME/.config/kitty/
		fi
}
set_term_config

# Firefox theme
firefox_profiles() {
	THEME_DIR="$HOME/.mozilla/FoxThemes"
	DEST_DIR="$HOME/.mozilla/firefox/"

if [[ $(grep '\[Profile[^0]\]' "$HOME"/.mozilla/firefox/profiles.ini) ]]; then 
	PROFPATH=$(grep -E '^\[Profile|^Path|^Default' "$HOME"/.mozilla/firefox/profiles.ini | grep -1 '^Default=1' | grep '^Path' | cut -c6-)
	cp -rf "$THEME_DIR"/* "$DEST_DIR"/"$PROFPATH"
else 
	PROFPATH=$(grep 'Path=' "$HOME"/.mozilla/firefox/profiles.ini | sed 's/^Path=//')
	cp -rf "$THEME_DIR"/* "$DEST_DIR"/"$PROFPATH"
fi
}
firefox_profiles

# Set dunst config
set_dunst_config() {
    dunst_path="$HOME/.config/i3/rices/$RICETHEME/dunst/dunstrc"
    if [ -f "$dunst_path" ]; then
        cp -rf "$dunst_path" ~/.config/dunst/

        # Проверяем, запущены ли dunst и musnify-mpd
        pid="$(ps aux | grep dunstrc | grep -v grep | awk '{print $2}')"
        pid2="$(ps aux | grep musnify-mpd | grep -v grep | awk '{print $2}')"

        # Останавливаем процессы, если они запущены
        if [ -n "$pid" ]; then
            kill -9 "$pid"
        fi
        if [ -n "$pid2" ]; then
            kill -9 "$pid2"
        fi

        # Запускаем dunst и musnify-mpd с новой конфигурацией
        dunst -conf ~/.config/dunst/dunstrc &
        musnify-mpd &
    else
        echo "Color file not exist!"
    fi
}
set_dunst_config

###---Global. Change colors for Tabbed
tabbed_settings() {
tabbed_path=""$HOME"/.config/i3/rices/$RICETHEME/tabbed/colors"
       if [ -f "$tabbed_path" ]; then
         cp -rf "$tabbed_path" "$i3_configd"
       else
         echo "Color file not exist!"
       fi
}
tabbed_settings

xresources_color() {
	if [ -f "$HOME/.Xresources.d/colors" ]; then
	 echo '' >  "$HOME/.Xresources.d/colors"
	 cat "$HOME/.Xresources.d/themes/$RICETHEME" > "$HOME/.Xresources.d/colors"
	 xrdb  ~/.Xresources
	fi
}
xresources_color

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

DPI=$(xrdb -query | sed -nE 's/^Xft\.dpi:\s*//p')
# HEIGHT=$((26 * DPI / 96))
#xrdb -merge $HOME/.Xresources.d/themes/mocha.Xresources
# Launch the bar
launch_bars() {

	for mon in $(polybar --list-monitors | cut -d":" -f1); do
		MONITOR=$mon polybar -q main -c "${rice_dir}"/config.ini &
		MONITOR=$mon polybar -q secondary -c "${rice_dir}"/config.ini &
	done
}
launch_bars