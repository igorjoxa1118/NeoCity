#!/usr/bin/env sh

WIRELESS_NAME=$(find /sys/class/net -name 'wl*' | sed 's#.*/##')
ETH_NAME=$(find /sys/class/net -name 'e*' | sed 's#.*/##')
export WIRELESS_NAME
export ETH_NAME
