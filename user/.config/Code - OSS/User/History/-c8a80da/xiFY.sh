#!/bin/bash

nvidia_detect()
{
    if [ `lspci -k | grep -A 2 -E "(VGA|3D)" | grep -i nvidia | wc -l` -gt 0 ]
    then
        #echo "nvidia card detected..."
        return 0
    else
        #echo "nvidia card not detected..."
        return 1
    fi
}


    #--------------------------------#
    # add nvidia drivers to the list #
    #--------------------------------#
    if nvidia_detect; then

        cat /usr/lib/modules/*/pkgbase | while read krnl; do
            echo "${krnl}-headers" >>install_pkg.lst
        done

        echo -e "nvidia-dkms\nnvidia-utils" >>install_pkg.lst
        sed -i "s/^hyprland-git/hyprland-nvidia-git/g" install_pkg.lst

    else
        echo "nvidia card not detected, skipping nvidia drivers..."
    fi

    if nvidia_detect && [ $(grep '^source = ~/.config/hypr/nvidia.conf' ${HOME}/.config/hypr/hyprland.conf | wc -l) -eq 0 ] ; then
    cp ${CfgDir}/.config/hypr/nvidia.conf ${HOME}/.config/hypr/nvidia.conf
    echo -e 'source = ~/.config/hypr/nvidia.conf # auto sourced vars for nvidia\n' >> ${HOME}/.config/hypr/hyprland.conf
fi