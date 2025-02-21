#!/bin/sh

set -eo pipefail

# Shell script to prepend i3status with ncmpc song

i3status | while :
do
        read line
        echo "$(ncmpcpp --current-song) | $line" || exit 1
done
