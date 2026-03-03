#!/usr/bin/env sh

# Пути (адаптировано для i3)
export scrDir="$(dirname "$(realpath "$0")")"
export confDir="$HOME/.config/waybar"  # Путь к конфигам Waybar
waybar_dir="$confDir"
modules_dir="$waybar_dir/modules"
conf_file="$waybar_dir/config.jsonc"
conf_ctl="$waybar_dir/config.ctl"

# Чтение управляющего файла
readarray -t read_ctl < "$conf_ctl"
num_files="${#read_ctl[@]}"
switch=0

# Переключение режимов (Next/Previous)
if [ "$num_files" -gt 1 ]; then
    for ((i=0; i<num_files; i++)); do
        flag=$(echo "${read_ctl[i]}" | cut -d '|' -f 1)
        if [ "$flag" -eq 1 ] && [ "$1" = "n" ]; then
            nextIndex=$(( (i + 1) % num_files ))
            switch=1
            break
        elif [ "$flag" -eq 1 ] && [ "$1" = "p" ]; then
            nextIndex=$((i - 1))
            switch=1
            break
        fi
    done
fi

# Обновление control-файла
if [ "$switch" -eq 1 ]; then
    update_ctl="${read_ctl[nextIndex]}"
    reload_flag=1
    sed -i "s/^1/0/g" "$conf_ctl"
    awk -F '|' -v cmp="$update_ctl" '{OFS=FS} {if($0==cmp) $1=1; print$0}' "$conf_ctl" > "$waybar_dir/tmp" && mv "$waybar_dir/tmp" "$conf_ctl"
fi

# Глобальные переменные для i3
export set_sysname=$(hostname)
export w_position=$(grep '^1|' "$conf_ctl" | cut -d '|' -f 3)
export w_height=$(grep '^1|' "$conf_ctl" | cut -d '|' -f 2)

# Дефолтная высота, если не задана
if [ -z "$w_height" ]; then
    y_monres=$(xrandr | grep '*' | head -n 1 | awk '{print $1}' | cut -d 'x' -f 2)
    export w_height=$(( y_monres * 2 / 100 ))
fi

# Размеры иконок
export i_size=$(( w_height * 6 / 10 ))
[ "$i_size" -lt 12 ] && export i_size=12
export i_task=$(( w_height * 6 / 10 ))
[ "$i_task" -lt 16 ] && export i_task=16
export i_priv=$(( w_height * 6 / 13 ))
[ "$i_priv" -lt 12 ] && export i_priv=12

# Тема иконок (для i3)
export i_theme=$(gsettings get org.gnome.desktop.interface icon-theme | sed "s/'//g")

# Генерация конфига
envsubst < "$modules_dir/header.jsonc" > "$conf_file"

# Функция генерации модулей
gen_mod() {
    local pos=$1
    local col=$2
    local mod=""

    mod=$(grep '^1|' "$conf_ctl" | cut -d '|' -f "${col}")
    mod="${mod//(/"custom/l_end"}"
    mod="${mod//)/"custom/r_end"}"
    mod="${mod//[/"custom/sl_end"}"
    mod="${mod//]/"custom/sr_end"}"
    mod="${mod//\{/"custom/rl_end"}"
    mod="${mod//\}/"custom/rr_end"}"
    mod="${mod// /\"\",\"\"}"

    echo -e "\t\"modules-${pos}\": [\"custom/padd\",\"${mod}\",\"custom/padd\"]," >> "$conf_file"
    echo "$mod" | tr ',' '\n' | sed 's/"//g' | awk '!x[$0]++' >> "$waybar_dir/modules.list"
}

# Генерация модулей
echo -e "\n\n// Generated modules //\n" >> "$conf_file"
gen_mod left 4
gen_mod center 5
gen_mod right 6

# Копирование модулей
while read -r mod_cpy; do
    [ -f "$modules_dir/$mod_cpy.jsonc" ] && envsubst < "$modules_dir/$mod_cpy.jsonc" >> "$conf_file"
done < "$waybar_dir/modules.list"

# Добавление футера
cat "$modules_dir/footer.jsonc" >> "$conf_file"

# Перезапуск Waybar
if [ "$reload_flag" = "1" ]; then
    killall -q waybar
    waybar --config "$conf_file" --style "$waybar_dir/style.css" >/dev/null 2>&1 &
fi