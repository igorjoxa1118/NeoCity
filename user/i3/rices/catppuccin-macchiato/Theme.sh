#!/usr/bin/env bash

## Catppuccin mocha

# Логирование
LOG_FILE="$HOME/.config/i3/logs/theme_script.log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "Запуск скрипта: $(date)" > "$LOG_FILE"

# Функция для логирования
log() {
    echo "$(date): $1" >> "$LOG_FILE"
}

# Проверка на параллельный запуск
LOCK_FILE="/tmp/i3_theme_script.lock"
if [ -f "$LOCK_FILE" ]; then
    log "Ошибка: Скрипт уже выполняется (lock-файл существует). Выход."
    exit 1
fi

# Создание lock-файла
touch "$LOCK_FILE"
trap 'rm -f "$LOCK_FILE"; log "Lock-файл удален."' EXIT

log "Lock-файл создан. Скрипт запущен."

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
log "Завершение процессов polybar и eww..."
killall -q polybar
killall -q eww
log "Процессы polybar и eww завершены."

###--Start rice

# Функция для настройки цветов Rofi Launcher
rofi_launcher_color() {
    log "Настройка цветов Rofi Launcher..."
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
    log "Настройка цветов Rofi Launcher завершена."
}

log "Настройка Rofi Launcher..."
rofi_launcher_color
log "Настройка Rofi Launcher завершена."

# Функция для настройки Rofi Powermenu
rofi_powermenu() {
    local powermenu_file="$HOME/.config/i3/src/powermenu/type-4/style-5.rasi"

    if [ -f "$powermenu_file" ]; then
        echo '' > "$powermenu_file"
        sed -i '/\/\*\*\*\*----- Global Properties -----\*\*\*\*\//,/}/d' "$powermenu_file"
        check_error "Не удалось удалить старый блок кода в $powermenu_file"

        cat << 'EOF' >> "$powermenu_file"
/**
 *
 * Author : Aditya Shakya (adi1090x)
 * Github : @adi1090x
 * 
 * Rofi Theme File
 * Rofi Version: 1.7.3
 **/

/*****----- Configuration -----*****/
configuration {
    show-icons:                 false;
}

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
    gradient-1:                  linear-gradient(45, #89b4fa, #a6e3a1);
    gradient-2:                  linear-gradient(0, #eba0ac, #7A72EC);
    gradient-3:                  linear-gradient(70, #f9e2af, #eba0ac);
    gradient-4:                  linear-gradient(135, #74c7ec, #89b4fa);
    gradient-5:                  linear-gradient(to left, #bdc3c7, #2c3e50);
    gradient-6:                  linear-gradient(to right, #1e1e2e, #1e1e2e, #1e1e2e);
    gradient-7:                  linear-gradient(to top, #74c7ec, #cba6f7, #eba0ac);
    gradient-8:                  linear-gradient(to bottom, #f38ba8, #493240);
    gradient-9:                  linear-gradient(0, #1a2a6c, #eba0ac, #f9e2af);
    gradient-10:                 linear-gradient(0, #283c86, #a6e3a1);
    gradient-11:                 linear-gradient(0, #89b4fa, #79CBCA, #E684AE);
    gradient-12:                 linear-gradient(0, #ff6e7f, #bfe9ff);
    gradient-13:                 linear-gradient(0, #f38ba8, #eba0ac);
    gradient-14:                 linear-gradient(0, #cba6f7, #cba6f7);
    gradient-15:                 linear-gradient(0, #a6e3a1, #a6e3a1);
    gradient-16:                 linear-gradient(0, #232526, #414345);
    gradient-17:                 linear-gradient(0, #833ab4, #eba0ac, #f9e2af);
    gradient-18:                 linear-gradient(0, #89b4fa, #74c7ec, #74c7ec, #89b4fa);
    gradient-19:                 linear-gradient(0, #03001e, #cba6f7, #ec38bc, #fdeff9);
    gradient-20:                 linear-gradient(0, #eba0ac, #061161);
    
    green:        #a6e3a1;
    
    background-window:           var(gradient-6);
    background-normal:           #1e1e2e;
    background-selected:         #89b4fa;
    foreground-normal:           #cdd6f4;
    foreground-selected:         #1e1e2e;
}

/*****----- Main Window -----*****/
window {
    transparency:                "real";
    location:                    center;
    anchor:                      center;
    fullscreen:                  true;
    cursor:                      "default";
    background-image:            var(background-window);
}

/*****----- Main Box -----*****/
mainbox {
    enabled:                     true;
    spacing:                     var(mainbox-spacing);
    margin:                      var(mainbox-margin);
    background-color:            transparent;
    children:                    [ "dummy", "userimage", "inputbar", "listview", "message", "dummy" ];
}

/*****----- User -----*****/
userimage {
    margin:                      0px 400px;
    border:                      2px;
    border-radius:               100%;
    border-color:              #eba0ac;
    background-color:            transparent;
    background-image:            url("~/.config/i3/src/powermenu/img/user/vir0id.jpg", both);
}

/*****----- Inputbar -----*****/
inputbar {
    enabled:                     true;
    background-color:            transparent;
    children:                    [ "dummy", "prompt", "dummy"];
}

dummy {
    background-color:            transparent;
}

prompt {
    enabled:                     true;
    font:                        var(prompt-font);
    background-color:            transparent;
    text-color:                  var(foreground-normal);
}

/*****----- Message -----*****/
message {
    enabled:                     true;
    margin:                      var(message-margin);
    padding:                     var(message-padding);
    border-radius:               var(message-border-radius);
    background-color:            var(background-normal);
    text-color:                  var(green);
}
textbox {
    font:                        var(textbox-font);
    background-color:            transparent;
    text-color:                  inherit;
    vertical-align:              0.5;
    horizontal-align:            0.5;
}

/*****----- Listview -----*****/
listview {
    enabled:                     true;
    expand:                      false;
    columns:                     5;
    lines:                       1;
    cycle:                       true;
    dynamic:                     true;
    scrollbar:                   false;
    layout:                      vertical;
    reverse:                     false;
    fixed-height:                true;
    fixed-columns:               true;
    
    spacing:                     var(listview-spacing);
    background-color:            transparent;
    cursor:                      "default";
}

/*****----- Elements -----*****/
element {
    enabled:                     true;
    padding:                     var(element-padding);
    border-radius:               var(element-border-radius);
    background-color:            var(background-normal);
    text-color:                  var(foreground-normal);
    cursor:                      pointer;
}
element-text {
    font:                        var(element-text-font);
    background-color:            transparent;
    text-color:                  inherit;
    cursor:                      inherit;
    vertical-align:              0.5;
    horizontal-align:            0.5;
}
element selected.normal {
    background-color:            var(background-selected);
    text-color:                  var(foreground-selected);
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

# Объединенная функция для настройки GTK темы, иконок и курсоров
set_gtk_theme_icons_cursor() {
    local xsettings_conf="$HOME/.xsettingsd"
    local gtk2_config="$HOME/.gtkrc-2.0"
    local gtk3_config="$HOME/.config/gtk-3.0/settings.ini"
    local gtk4_config="$HOME/.config/gtk-4.0/settings.ini"
    local default_cursor_file="$HOME/.icons/default/index.theme"

    # Определяем иконки и курсоры в зависимости от темы
    case "$RICETHEME" in
        "catppuccin-mocha")
            ICON_THEME="TokyoNight-SE"
            CURSOR_THEME="catppuccin-mocha-blue-cursors"
            ;;
        "catppuccin-latte")
            ICON_THEME="Magna-Dark-Icons"
            CURSOR_THEME="catppuccin-mocha-maroon-cursors"
            ;;
        "catppuccin-frappe")
            ICON_THEME="Catppuccin-Frappe"
            CURSOR_THEME="catppuccin-mocha-mauve-cursors"
            ;;
        "catppuccin-macchiato")
            ICON_THEME="Catppuccin-Macchiato"
            CURSOR_THEME="catppuccin-mocha-peach-cursors"
            ;;
        *)
            ICON_THEME="Adwaita"
            CURSOR_THEME="Adwaita"
            ;;
    esac

    # Применяем настройки через xsettingsd (здесь кавычки нужны)
    echo -e "Net/ThemeName \"$RICETHEME\"
Net/IconThemeName \"$ICON_THEME\"
Gtk/CursorThemeName \"$CURSOR_THEME\"" > "$xsettings_conf"

    # Для .gtkrc-2.0 - добавляем кавычки
    if [ -f "$gtk2_config" ]; then
        sed -i \
            -e "s/gtk-theme-name=.*/gtk-theme-name=\"$RICETHEME\"/g" \
            -e "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=\"$ICON_THEME\"/g" \
            -e "s/gtk-font-name=.*/gtk-font-name=\"MesloLGS NF Regular 10\"/g" \
            -e "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=\"$CURSOR_THEME\"/g" \
            -e 's/gtk-xft-hintstyle=.*/gtk-xft-hintstyle="hintmedium"/g' \
            -e 's/gtk-xft-rgba=.*/gtk-xft-rgba="rgb"/g' \
            "$gtk2_config"
    fi

    # Для gtk-3.0/settings.ini - без кавычек
    if [ -f "$gtk3_config" ]; then
        sed -i \
            -e "s/gtk-theme-name=.*/gtk-theme-name=$RICETHEME/g" \
            -e "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=$ICON_THEME/g" \
            -e "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=$CURSOR_THEME/g" \
            "$gtk3_config"
    fi

    # Для gtk-4.0/settings.ini - без кавычек
    if [ -f "$gtk4_config" ]; then
        sed -i \
            -e "s/gtk-theme-name=.*/gtk-theme-name=$RICETHEME/g" \
            -e "s/gtk-icon-theme-name=.*/gtk-icon-theme-name=$ICON_THEME/g" \
            -e "s/gtk-cursor-theme-name=.*/gtk-cursor-theme-name=$CURSOR_THEME/g" \
            "$gtk4_config"
    fi

    # Обновляем курсор по умолчанию
    [ -f "$default_cursor_file" ] && sed -i "s/Inherits=.*/Inherits=$CURSOR_THEME/" "$default_cursor_file"

    # Применяем через gsettings (здесь кавычки нужны)
    if command -v gsettings >/dev/null; then
        gsettings set org.gnome.desktop.interface gtk-theme "$RICETHEME"
        gsettings set org.gnome.desktop.interface icon-theme "$ICON_THEME"
        gsettings set org.gnome.desktop.interface cursor-theme "$CURSOR_THEME"
    fi
    # Обновление кэша GTK
    gtk-update-icon-cache -f ~/.local/share/icons/*
    gtk-update-icon-cache -f /usr/share/icons/*
    # Перезапускаем xsettingsd
    pkill -x xsettingsd && xsettingsd &
}

# Вызов объединенной функции
set_gtk_theme_icons_cursor

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
    local tabbed_path="$rice_dir/tabbed/colors.conf"

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

# Функция для настройки темы Visual Studio Code
vscode_theme() {
    local vscode_settings="$HOME/.config/Code - OSS/User/settings.json"
    local vscode_theme

    # Определение темы VS Code в зависимости от текущего риса
    case "$RICETHEME" in
        "catppuccin-mocha")
            vscode_theme="Catppuccin Mocha"
            ;;
        "catppuccin-macchiato")
            vscode_theme="Catppuccin Macchiato"
            ;;
        "catppuccin-latte")
            vscode_theme="Catppuccin Latte"
            ;;
        "catppuccin-frappe")
            vscode_theme="Catppuccin Frappé"
            ;;
        *)
            log "Тема $RICETHEME не поддерживается для настройки VS Code."
            return 1
            ;;
    esac

    # Проверка существования файла настроек VS Code
    if [ -f "$vscode_settings" ]; then
        # Изменение темы в файле настроек
        jq --arg theme "$vscode_theme" '."workbench.colorTheme" = $theme' "$vscode_settings" > "$vscode_settings.tmp"
        check_error "Не удалось изменить тему в $vscode_settings"
        mv "$vscode_settings.tmp" "$vscode_settings"
        check_error "Не удалось обновить файл настроек VS Code"
    else
        log "Файл настроек VS Code $vscode_settings не найден!"
    fi
}

# Вызов функции для настройки темы VS Code
vscode_theme

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

# Функция для настройки цветов mpd_scroller.sh
set_mpd_scroller_colors() {
    local mpd_scroller_path="$HOME/.config/i3/src/mpd_scroller.sh"
    log "Проверка пути: $mpd_scroller_path"

    # Проверка существования файла
    if [ ! -f "$mpd_scroller_path" ]; then
        log "Ошибка: mpd_scroller.sh не найден!"
        return 1
    fi

    # Защита от симлинков
    if [[ -L "$mpd_scroller_path" ]]; then
        log "Ошибка: $mpd_scroller_path — это символическая ссылка!"
        return 1
    fi

    # Определение цветов темы
    case "$RICETHEME" in
        "catppuccin-mocha")
            COLOR_PLAYING="#a6e3a1"   # Зеленый
            COLOR_PAUSED="#f38ba8"    # Красный
            COLOR_STOPPED="#f9e2af"   # Желтый
            COLOR_OFFLINE="#bac2de"   # Серый
            COLOR_TEXT="#cdd6f4"      # Основной текст
            ;;
        "catppuccin-frappe")
            COLOR_PLAYING="#a6d189"   # Зеленый
            COLOR_PAUSED="#e5c890"    # Желтый
            COLOR_STOPPED="#e78284"   # Красный
            COLOR_OFFLINE="#a5adce"   # Серый
            COLOR_TEXT="#c6d0f5"      # Основной текст
            ;;
        "catppuccin-macchiato")
            COLOR_PLAYING="#8bd5ca"   # Зеленый
            COLOR_PAUSED="#eed49f"    # Желтый
            COLOR_STOPPED="#ed8796"   # Красный
            COLOR_OFFLINE="#b8c0e0"   # Серый
            COLOR_TEXT="#cad3f5"      # Основной текст
            ;;
        "catppuccin-latte")
            COLOR_PLAYING="#40a02b"   # Зеленый
            COLOR_PAUSED="#df8e1d"    # Желтый
            COLOR_STOPPED="#d20f39"   # Красный
            COLOR_OFFLINE="#7c7f93"   # Серый
            COLOR_TEXT="#4c4f69"      # Основной текст
            ;;
        *)
            log "Тема $RICETHEME не поддерживается!"
            return 1
            ;;
    esac

    # Создание временного файла с новыми настройками
    local temp_file=$(mktemp)
    cat << EOF > "$temp_file"
# Цвета (Catppuccin $RICETHEME)
COLOR_PLAYING="$COLOR_PLAYING"   # Зеленый
COLOR_PAUSED="$COLOR_PAUSED"    # Желтый
COLOR_STOPPED="$COLOR_STOPPED"   # Красный
COLOR_OFFLINE="$COLOR_OFFLINE"   # Серый
COLOR_TEXT="$COLOR_TEXT"      # Основной текст
EOF

    # Резервное копирование оригинального файла
    cp "$mpd_scroller_path" "${mpd_scroller_path}.bak"
    log "Создана резервная копия: ${mpd_scroller_path}.bak"

    # Обновление цветов в файле
    log "Обновление цветов в $mpd_scroller_path"
    sed -i '/^# Цвета (Catppuccin/,/^# ===== ФУНКЦИИ =====/ {
        /^# Цвета (Catppuccin/ {
            r '"$temp_file"'
            d
        }
        /^# ===== ФУНКЦИИ =====/!d
    }' "$mpd_scroller_path" || {
        log "Ошибка sed при изменении $mpd_scroller_path"
        return 1
    }

    # Очистка временного файла
    rm "$temp_file"
    log "Цвета успешно обновлены в $mpd_scroller_path"
}

# Вызов функции для настройки цветов mpd_scroller.sh
set_mpd_scroller_colors

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

log "Скрипт для Macchiato успешно завершен!"