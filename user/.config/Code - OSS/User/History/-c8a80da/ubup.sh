#!/bin/bash

nvidia_detect()
{
    if [ `lspci -k | grep -A 2 -E "(VGA|3D)" | grep -i nvidia | wc -l` -gt 0 ]
    then
        echo "nvidia card detected..."
        #return 0
    else
        echo "nvidia card not detected..."
        #return 1
    fi
}

nvidia_detect