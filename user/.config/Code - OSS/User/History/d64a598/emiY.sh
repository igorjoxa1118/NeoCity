#!/bin/bash

## calamares shellprocess_settings.conf
# run chroot

mkdir /media

haveged -w 1024
pacman-key --init
pkill haveged
pacman-key --populate

cat <<LOL >>/etc/pacman.d/gnupg/gpg.conf
keyserver hkps://hkps.pool.sks-keyservers.net:443
keyserver hkp://ipv4.pool.sks-keyservers.net:11371
keyserver hkp://pgp.mit.edu
keyserver hkp://keys.gnupg.net
keyserver hkp://keyserver.ubuntu.com
LOL

rm /usr/local/bin/settings.sh