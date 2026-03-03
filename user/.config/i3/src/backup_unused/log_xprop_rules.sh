#!/bin/bash
LOG_FILE="$HOME/.config/i3/logs/window_rules.log"
DEBUG_FILE="$HOME/.config/i3/logs/debug.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Запись сырых данных и времени
echo "=== DEBUG START ===" > "$DEBUG_FILE"
while read -r event; do
    echo "$(date '+%H:%M:%S') RAW EVENT: $event" >> "$DEBUG_FILE"
    
    # Попробуем разные варианты парсинга
    window_class=$(echo "$event" | jq -r '.container.window_properties.class? // .window_properties.class? // empty')
    workspace=$(echo "$event" | jq -r '.container.workspace.name? // .workspace? // empty')
    
    echo "$(date '+%H:%M:%S') PARSED: class=$window_class workspace=$workspace" >> "$DEBUG_FILE"
    
    if [[ -n "$window_class" ]]; then
        echo "$(date '+%a %d %b %Y %H:%M:%S %Z') $window_class → $workspace" >> "$LOG_FILE"
    fi
done < <(i3-msg -t subscribe -m '[ "window" ]')