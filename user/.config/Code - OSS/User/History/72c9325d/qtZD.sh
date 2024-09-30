#!/usr/bin/env bash

    # add nvidia drivers to the list #
    #--------------------------------#
    if nvidia_detect; then
        cat /usr/lib/modules/*/pkgbase | while read krnl; do
            echo "${krnl}-headers" >>install_pkg.lst
        done
        IFS=$' ' read -r -d '' -a nvga < <(lspci -k | grep -E "(VGA|3D)" | grep -i nvidia | awk -F ':' '{print $NF}' | tr -d '[]()' && printf '\0')
        for nvcode in "${nvga[@]}"; do
            awk -F '|' -v nvc="${nvcode}" '{if ($3 == nvc) {split(FILENAME,driver,"/"); print driver[length(driver)],"\nnvidia-utils"}}' .nvidia/nvidia*dkms >>install_pkg.lst
        done
        echo -e "\033[0;32m[GPU]\033[0m: detected // ${nvga[@]}"
    else
        echo "nvidia card not detected, skipping nvidia drivers..."
    fi