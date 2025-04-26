#!/usr/bin/env bash

## Catppuccin mocha

read -r RICETHEME < "$HOME/.config/i3/config.d/.rice"
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
i3_configd="$HOME/.config/i3/config.d"
i3_scr="$HOME/.config/i3/src"

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