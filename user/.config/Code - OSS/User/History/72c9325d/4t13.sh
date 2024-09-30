#!/usr/bin/env bash
clone_yay() {
    if [[ -d "$HOME/Download" ]]; then
       git clone $yay_git "$HOME/Download"
       cd paru
    else
       cd "$HOME"
       git clone $yay_git
       cd paru
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