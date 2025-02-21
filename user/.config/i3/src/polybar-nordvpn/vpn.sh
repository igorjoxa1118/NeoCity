#!/bin/bash

# Display Status Function
display_status() {
    # Call nordvpn status and settings once and store the output
    local status_output=$(nordvpn status)
    local settings_output=$(nordvpn settings)

    # Parse the stored output
    local status=$(echo "$status_output" | awk -F': ' '/Status/ {print $2}')
    local location=$(echo "$status_output" | awk -F': ' '/City/ {print $2}')
    local transfer=$(echo "$status_output" | awk -F': ' '/Transfer/ {print $2}')
    local killswitch=$(echo "$settings_output" | awk -F': ' '/Kill Switch/ {print $2}')

    # Conditional display 
    if [[ "$status" == "Connected" ]]; then
        echo "ON"
    else
        echo "OFF"
    fi
}
# Toggle Kill switch Function
toggle_killswitch() {
    local killswitch_status=$(nordvpn settings | awk '/Kill Switch/ {print $3}')
    if [ "$killswitch_status" = "enabled" ]; then
        nordvpn set killswitch disable
    else
        nordvpn set killswitch enable
    fi
}

# Main Function
case "$1" in
    toggle)
        toggle_killswitch
        ;;
    *)
        display_status
        ;;
esac