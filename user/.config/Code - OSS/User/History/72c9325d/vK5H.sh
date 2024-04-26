#!/usr/bin/env bash

yay_git="https://aur.archlinux.org/paru.git"


clone_yay() {
    if [[ -d "$HOME/Download" ]]; then
       git clone $yay_git "$HOME/Download"
       cd paru
       exit;
    else
       cd "$HOME"
       git clone $yay_git
       cd paru
       exit;
    fi
}

while true; do
	read -rp " Do you want yay? [y/N]: " yn
		case $yn in
			[Yy]* ) clone_yay;;
			[Nn]* ) break;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear