#!/usr/bin/env bash

## Sweet-Dark Rice Theme Script

# Пути
RICETHEME="Sweet-Dark"
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_configd="$HOME/.config/i3/config.d"
i3_scr="$HOME/.config/i3/src"

# 1. Внешний вид
apply_appearance() {
    gsettings set org.gnome.desktop.interface gtk-theme "Sweet-Dark"
    gsettings set org.gnome.desktop.interface icon-theme "candy-icons"
    gsettings set org.gnome.desktop.interface cursor-theme "Sweet"
}

# 2. Picom (запуск из твоего пути)
launch_picom() {
    pkill picom
    sleep 0.3
    # Проверяем наличие твоего основного конфига
    if [ -f "$i3_configd/picom.conf" ]; then
        picom --config "$i3_configd/picom.conf" &
    else
        picom &
    fi
}

# 3. Цвета MPD Scroller
set_mpd_scroller_colors() {
    local mpd_scroller_path="$i3_scr/mpd_scroller.sh"
    [ ! -f "$mpd_scroller_path" ] && return
    
    local temp_file=$(mktemp)
    cat << EOF > "$temp_file"
# Цвета (Sweet-Dark)
COLOR_PLAYING="#00ffcc"
COLOR_PAUSED="#ff00ff"
COLOR_STOPPED="#ed254e"
COLOR_OFFLINE="#555555"
COLOR_TEXT="#f1fffa"
EOF

    sed -i '/^# Цвета/,/^# ===== ФУНКЦИИ =====/ {
        /^# Цвета/ {
            r '"$temp_file"'
            d
        }
        /^# ===== ФУНКЦИИ =====/!d
    }' "$mpd_scroller_path"
    rm "$temp_file"
}

# --- Старт ---
pkill polybar
pkill dunst

apply_appearance
set_mpd_scroller_colors
launch_picom

# Dunst
dunst -config "$rice_dir/dunst/dunstrc" &

# Polybar
polybar -q main -c "$rice_dir/config.ini" &

# Обои
feh --bg-fill --randomize "$rice_dir/walls/dark/" &

echo "Sweet-Dark применен успешно!"