#!/usr/bin/env bash

## Catppuccin mocha

# Логирование
LOG_FILE="/tmp/theme_script.log"
echo "Запуск скрипта: $(date)" > "$LOG_FILE"

# Функция для логирования
log() {
    echo "$(date): $1" >> "$LOG_FILE"
}

# Функция для проверки ошибок
check_error() {
    if [ $? -ne 0 ]; then
        log "Ошибка: $1"
        exit 1
    fi
}

# Чтение текущей темы
if [ ! -f "$HOME/.config/i3/config.d/.rice" ]; then
    log "Файл .rice не найден!"
    exit 1
fi

read -r RICETHEME < "$HOME/.config/i3/config.d/.rice"
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_configd="$HOME/.config/i3/config.d"
i3_scr="$HOME/.config/i3/src"

# Проверка существования директории темы
if [ ! -d "$rice_dir" ]; then
    log "Директория темы $rice_dir не найдена!"
    exit 1
fi

# Убиваем запущенные процессы polybar и eww
killall -q polybar
killall -q eww

###--Start rice

# Функция для настройки цветов Rofi Launcher
rofi_launcher_color() {
    local colors_file="$HOME/.config/i3/src/launchers/type-3/shared/colors.rasi"
    local source_colors="$rice_dir/rofi/shared/colors.rasi"

    if [ -f "$colors_file" ]; then
        echo '' > "$colors_file"
        check_error "Не удалось очистить файл $colors_file"

        if [ -f "$source_colors" ]; then
            cat "$source_colors" > "$colors_file"
            check_error "Не удалось скопировать цвета Rofi из $source_colors"
        else
            log "Файл цветов Rofi $source_colors не найден!"
        fi
    else
        log "Файл $colors_file не найден!"
    fi
}
rofi_launcher_color

# Функция для настройки Rofi Powermenu
rofi_powermenu() {
    local powermenu_file="$HOME/.config/i3/src/powermenu/type-4/style-5.rasi"

    if [ -f "$powermenu_file" ]; then
        sed -i '/\/\*\*\*\*----- Global Properties -----\*\*\*\*\//,/}/d' "$powermenu_file"
        check_error "Не удалось удалить старый блок кода в $powermenu_file"

        cat << 'EOF' >> "$powermenu_file"
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
    gradient-1:                  linear-gradient(45, #ee99a0, #a6e3a1);
    gradient-2:                  linear-gradient(0, #ee99a0, #7A72EC);
    gradient-3:                  linear-gradient(70, #f9e2af, #ee99a0);
    gradient-4:                  linear-gradient(135, #74c7ec, #ee99a0);
    gradient-5:                  linear-gradient(to left, #bdc3c7, #2c3e50);
    gradient-6:                  linear-gradient(to right, #24273a, #24273a, #24273a);
    gradient-7:                  linear-gradient(to top, #74c7ec, #cba6f7, #ee99a0);
    gradient-8:                  linear-gradient(to bottom, #f38ba8, #493240);
    gradient-9:                  linear-gradient(0, #1a2a6c, #ee99a0, #f9e2af);
    gradient-10:                 linear-gradient(0, #283c86, #a6e3a1);
    gradient-11:                 linear-gradient(0, #ee99a0, #79CBCA, #E684AE);
    gradient-12:                 linear-gradient(0, #ff6e7f, #bfe9ff);
    gradient-13:                 linear-gradient(0, #f38ba8, #ee99a0);
    gradient-14:                 linear-gradient(0, #cba6f7, #cba6f7);
    gradient-15:                 linear-gradient(0, #a6e3a1, #a6e3a1);
    gradient-16:                 linear-gradient(0, #232526, #414345);
    gradient-17:                 linear-gradient(0, #833ab4, #ee99a0, #f9e2af);
    gradient-18:                 linear-gradient(0, #ee99a0, #74c7ec, #74c7ec, #ee99a0);
    gradient-19:                 linear-gradient(0, #03001e, #cba6f7, #ec38bc, #fdeff9);
    gradient-20:                 linear-gradient(0, #ee99a0, #061161);
    
    green:        #a6e3a1;
    bords:        #cba6f7;
    
    background-window:           var(gradient-6);
    background-normal:           #24273a;
    background-selected:         #ee99a0;
    foreground-normal:           #cdd6f4;
    foreground-selected:         #24273a;
}
EOF
        check_error "Не удалось добавить новый блок кода в $powermenu_file"
    else
        log "Файл $powermenu_file не найден!"
    fi
}
rofi_powermenu

# Функция для настройки цветов Rofi Calendar
rofi_calendar_color() {
    local colors_file="$i3_scr/rofi-calendar/themes/colors.rasi"
    local source_colors="$HOME/.config/i3/src/rofi-themes/colors/$RICETHEME.rasi"

    if [ -f "$colors_file" ]; then
        echo '' > "$colors_file"
        check_error "Не удалось очистить файл $colors_file"

        if [ -f "$source_colors" ]; then
            cat "$source_colors" > "$colors_file"
            check_error "Не удалось скопировать цвета Rofi Calendar из $source_colors"
        else
            log "Файл цветов Rofi Calendar $source_colors не найден!"
        fi
    else
        log "Файл $colors_file не найден!"
    fi
}
rofi_calendar_color

# Функция для настройки GTK темы
set_gtk_theme() {
    local xsettings_conf="$HOME/.xsettingsd"

    cat <<EOF > "$xsettings_conf"
Net/ThemeName "$RICETHEME"
Net/IconThemeName "Catppuccin-Macchiato"
Gtk/CursorThemeName "catppuccin-mocha-mauve-cursors"
EOF
    check_error "Не удалось создать файл конфигурации xsettingsd"

    if pgrep -x "xsettingsd" > /dev/null; then
        killall xsettingsd
        check_error "Не удалось завершить процесс xsettingsd"
    fi
    xsettingsd &
    check_error "Не удалось запустить xsettingsd"
}
set_gtk_theme

# Функция для настройки иконок
set_icons() {
    local gtk2_config="$HOME/.gtkrc-2.0"
    local gtk3_config="$HOME/.config/gtk-3.0/settings.ini"
    local gtk4_config="$HOME/.config/gtk-4.0/settings.ini"

    for config in "$gtk2_config" "$gtk3_config" "$gtk4_config"; do
        if [ -f "$config" ]; then
            sed -i "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=Catppuccin-Macchiato/g" "$config"
            check_error "Не удалось изменить иконки в $config"
        else
            log "Файл $config не найден!"
        fi
    done
}
set_icons

# Функция для настройки курсоров
set_cursor() {
    local gtk2_config="$HOME/.gtkrc-2.0"
    local gtk3_config="$HOME/.config/gtk-3.0/settings.ini"
    local gtk4_config="$HOME/.config/gtk-4.0/settings.ini"

    for config in "$gtk2_config" "$gtk3_config" "$gtk4_config"; do
        if [ -f "$config" ]; then
            sed -i "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=catppuccin-mocha-mauve-cursors/g" "$config"
            check_error "Не удалось изменить курсоры в $config"
        else
            log "Файл $config не найден!"
        fi
    done
}
set_cursor

# Функция для настройки цвета теней в Picom
set_picom_shadow_color() {
    local picom_config="$HOME/.config/i3/config.d/picom.conf"
    local shadow_color

    # Определение цвета теней в зависимости от темы
    case "$RICETHEME" in
        "catppuccin-mocha")
            shadow_color="#89b4fa"
            ;;
        "catppuccin-macchiato")
            shadow_color="#ee99a0"
            ;;
        "catppuccin-latte")
            shadow_color="#e64553"
            ;;
        "catppuccin-frappe")
            shadow_color="#ca9ee6"
            ;;
        *)
            log "Тема $RICETHEME не поддерживается для настройки цвета теней."
            return 1
            ;;
    esac

    # Проверка существования файла конфигурации Picom
    if [ -f "$picom_config" ]; then
        # Изменение цвета теней в конфигурации Picom
        sed -i "s/^shadow-color = .*/shadow-color = \"$shadow_color\";/g" "$picom_config"
        check_error "Не удалось изменить цвет теней в $picom_config"

        # Перезапуск Picom для применения изменений
        if pgrep -x "picom" > /dev/null; then
            killall picom
            check_error "Не удалось завершить процесс Picom"
        fi
        picom --config "$picom_config" &
        check_error "Не удалось запустить Picom"
    else
        log "Файл конфигурации Picom $picom_config не найден!"
    fi
}

# Вызов функции для настройки цвета теней в Picom
set_picom_shadow_color

# Функция для настройки NetworkManager
set_network_manager() {
    local netmanager_file="$HOME/.config/i3/src/rofi-themes/NetManagerDM.rasi"

    if [ -f "$netmanager_file" ]; then
        sed -i 's|@import "colors/catppuccin-[^"]*"|@import "colors/catppuccin-mocha.rasi"|g' "$netmanager_file"
        check_error "Не удалось изменить конфигурацию NetworkManager"
    else
        log "Файл $netmanager_file не найден!"
    fi
}
set_network_manager

# Функция для настройки терминалов
set_term_config() {
    local al_config_dir="$HOME/.config/alacritty"
    local al_rice_dir="$rice_dir/alacritty"
    local ki_config_dir="$HOME/.config/kitty"
    local ki_rice_dir="$rice_dir/kitty"

    if [ -f "$al_config_dir/alacritty.toml" ]; then
        rm -rf "$al_config_dir"/*
        check_error "Не удалось очистить директорию $al_config_dir"
        cp -rf "$al_rice_dir"/* "$al_config_dir"
        check_error "Не удалось скопировать конфигурацию Alacritty"
    fi

    if [ -f "$ki_config_dir/kitty.conf" ]; then
        cp -rf "$ki_rice_dir/kitty.conf" "$ki_config_dir"
        check_error "Не удалось скопировать конфигурацию Kitty"
    else
        cp -rf "$ki_rice_dir/kitty.conf" "$HOME/.config/kitty/"
        check_error "Не удалось скопировать конфигурацию Kitty"
    fi
}
set_term_config

# Функция для настройки Firefox
firefox_profiles() {
    local theme_dir="$HOME/.mozilla/FoxThemes"
    local dest_dir="$HOME/.mozilla/firefox/"

    if [[ $(grep '\[Profile[^0]\]' "$HOME/.mozilla/firefox/profiles.ini") ]]; then
        profpath=$(grep -E '^\[Profile|^Path|^Default' "$HOME/.mozilla/firefox/profiles.ini" | grep -1 '^Default=1' | grep '^Path' | cut -c6-)
        cp -rf "$theme_dir"/* "$dest_dir/$profpath"
        check_error "Не удалось скопировать тему Firefox"
    else
        profpath=$(grep 'Path=' "$HOME/.mozilla/firefox/profiles.ini" | sed 's/^Path=//')
        cp -rf "$theme_dir"/* "$dest_dir/$profpath"
        check_error "Не удалось скопировать тему Firefox"
    fi
}
firefox_profiles

# Функция для настройки Dunst
set_dunst_config() {
    local dunst_path="$rice_dir/dunst/dunstrc"

    if [ -f "$dunst_path" ]; then
        cp -rf "$dunst_path" ~/.config/dunst/
        check_error "Не удалось скопировать конфигурацию Dunst"

        pid="$(ps aux | grep dunstrc | grep -v grep | awk '{print $2}')"
        pid2="$(ps aux | grep musnify-mpd | grep -v grep | awk '{print $2}')"

        if [ -n "$pid" ]; then
            kill -9 "$pid"
            check_error "Не удалось завершить процесс Dunst"
        fi
        if [ -n "$pid2" ]; then
            kill -9 "$pid2"
            check_error "Не удалось завершить процесс musnify-mpd"
        fi

        dunst -conf ~/.config/dunst/dunstrc &
        check_error "Не удалось запустить Dunst"
        musnify-mpd &
        check_error "Не удалось запустить musnify-mpd"
    else
        log "Файл конфигурации Dunst $dunst_path не найден!"
    fi
}
set_dunst_config

# Функция для настройки Tabbed
tabbed_settings() {
    local tabbed_path="$rice_dir/tabbed/colors"

    if [ -f "$tabbed_path" ]; then
        cp -rf "$tabbed_path" "$i3_configd"
        check_error "Не удалось скопировать конфигурацию Tabbed"
    else
        log "Файл конфигурации Tabbed $tabbed_path не найден!"
    fi
}
tabbed_settings

# Функция замены цветов cava на акцентные catppuccin macchiato
cava_colors() {
sed -i '/colors=(/,/)/c\
colors=(\
    "#8aadf4" "#ed8796" "#f5a97f" "#a6da95" "#8bd5ca"\
    "#91d7e3" "#c6a0f6" "#f4dbd6" "#8aadf4" "#ed8796"\
    "#f5a97f" "#a6da95" "#8bd5ca" "#91d7e3" "#c6a0f6"\
)' "$HOME/.config/i3/src/cava.sh"
}
cava_colors

# Функция для настройки Xresources
xresources_color() {
    local xresources_colors="$HOME/.Xresources.d/colors"
    local xresources_theme="$HOME/.Xresources.d/themes/$RICETHEME"

    if [ -f "$xresources_colors" ]; then
        echo '' > "$xresources_colors"
        check_error "Не удалось очистить файл $xresources_colors"

        if [ -f "$xresources_theme" ]; then
            cat "$xresources_theme" > "$xresources_colors"
            check_error "Не удалось скопировать цвета Xresources"
            xrdb ~/.Xresources
            check_error "Не удалось применить Xresources"
        else
            log "Файл темы Xresources $xresources_theme не найден!"
        fi
    else
        log "Файл $xresources_colors не найден!"
    fi
}
xresources_color

# Ожидание завершения процессов polybar
while pgrep -u $UID -x polybar >/dev/null; do
    sleep 1
done

# Запуск Polybar
launch_bars() {
    for mon in $(polybar --list-monitors | cut -d":" -f1); do
        MONITOR=$mon polybar -q main -c "$rice_dir/config.ini" &
        check_error "Не удалось запустить Polybar на мониторе $mon"
        MONITOR=$mon polybar -q secondary -c "$rice_dir/config.ini" &
        check_error "Не удалось запустить Polybar на мониторе $mon"
    done
}
launch_bars

log "Скрипт успешно завершен!"