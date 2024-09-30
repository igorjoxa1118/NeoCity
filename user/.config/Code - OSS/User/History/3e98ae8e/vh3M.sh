#!/bin/bash
#set -x

CRE=$(tput setaf 1)
CYE=$(tput setaf 3)
CGR=$(tput setaf 2)
CBL=$(tput setaf 4)
BLD=$(tput bold)
CNC=$(tput sgr0)

backup_folder=~/.Backup_files
date=$(date +%Y%m%d-%H%M%S)
yay_git="https://aur.archlinux.org/paru.git"

logo () {
	
	local text="${1:?}"
	echo -en "                                  
____   ____.__        _______  .__    .___     .___      __    _____.__.__                  
\   \ /   /|__|______ \   _  \ |__| __| _/   __| _/_____/  |__/ ____\__|  |   ____   ______ 
 \   Y   / |  \_  __ \/  /_\  \|  |/ __ |   / __ |/  _ \   __\   __\|  |  | _/ __ \ /  ___/ 
  \     /  |  ||  | \/\  \_/   \  / /_/ |  / /_/ (  <_> )  |  |  |  |  |  |_\  ___/ \___ \  
   \___/   |__||__|    \_____  /__\____ |  \____ |\____/|__|  |__|  |__|____/\___  >____  > 
                             \/        \/       \/                               \/     \/  
                  _____              .__________                                            
                _/ ____\___________  |__\_____  \_  _  _______                              
                \   __\/  _ \_  __ \ |  | _(__  < \/ \/ /     \                             
                 |  | (  <_> )  | \/ |  |/       \     /  Y Y  \                            
                 |__|  \____/|__|    |__/______  /\/\_/|__|_|  /                            
                                               \/            \/                             \n"
    printf ' %s [%s%s %s%s %s]%s\n\n' "${CRE}" "${CNC}" "${CYE}" "${text}" "${CNC}" "${CRE}" "${CNC}"
}

########## ---------- You must not run this as root ---------- ##########

if [ "$(id -u)" = 0 ]; then
    echo "This script MUST NOT be run as root user."
    exit 1
fi

########## ---------- Welcome ---------- ##########

logo "Welcome!"
printf '%s%sThis script will check if you have the necessary dependencies, and if not, it will install them. Then, it will clone the RICE in your HOME directory.\nAfter that, it will create a secure backup of your files, and then copy the new files to your computer.\n\nMy dotfiles DO NOT modify any of your system configurations.\nYou will be prompted for your root password to install missing dependencies and/or to switch to zsh shell if its not your default.\n\nThis script doesnt have the potential power to break your system, it only copies files from my repository to your HOME directory.%s\n\n' "${BLD}" "${CRE}" "${CNC}"

while true; do
	read -rp " Do you wish to continue? [y/N]: " yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

dependencias=(base-devel yad cmus rsync mpv jq git socat mpd polkit-gnome stalonetray kitty lsd ranger \
              micro blueman ristretto thunar thunar-volman thunar-media-tags-plugin thunar-archive-plugin \
              polybar rofi dunst xdg-user-dirs nitrogen picom yt-dlp \
              fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-history-substring-search starship)

dependencias_yay=(zscroll-git ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling musikcube pamac-aur kazam)

is_installed() {
  pacman -Qi "$1" &> /dev/null
  return $?
}

########## ---------- Install packages ---------- ##########

printf "%s%sChecking for required packages...%s\n" "${BLD}" "${CBL}" "${CNC}"
for pkges in "${dependencias[@]}"
do
  if ! is_installed "$pkges"; then
    sudo pacman -S "$pkges" --noconfirm
    printf "\n"
  else
    printf '%s%s is already installed on your system!%s\n' "${CGR}" "$pkges" "${CNC}"
    sleep 1
  fi
done
sleep 3
clear

########## ---------- Preparing Folders ---------- ##########

# Проверка того, что архив user-dirs.dirs не существует в ~/.config
	if [ ! -e "$HOME/.config/user-dirs.dirs" ]; then
		xdg-user-dirs-update
		echo "Creating xdg-user-dirs"
	fi
sleep 2 
clear

########## ---------- Clone paru yay---------- ##########

clone_yay() {
    if [[ -d "$HOME/Download" ]]; then
       git clone $yay_git "$HOME/Download"
       makepkg -si
    else
       cd "$HOME"
       git clone $yay_git
       cd paru
       makepkg -si
    fi
}

while true; do
	read -rp " Do you want yay? [y/N]: " yn
		case $yn in
			[Yy]* ) clone_yay && break;;
			[Nn]* ) break;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

########## ---------- Install packages yay---------- ##########

is_installed_yay() {
  paru -Qi "$1" &> /dev/null
  return $?
}

printf "%s%sChecking for required packages...%s\n" "${BLD}" "${CBL}" "${CNC}"
for pkges_yay in "${dependencias_yay[@]}"
do
  if ! is_installed_yay "$pkges_yay"; then
    paru -S "$pkges_yay" --noconfirm
    printf "\n"
  else
    printf '%s%s is already installed on your system!%s\n' "${CGR}" "$pkges_yay" "${CNC}"
    sleep 1
  fi
done
sleep 3
clear

########## ---------- Cloning the Tokio night dots! ---------- ##########

logo "Downloading dotfiles"

repo_url="https://github.com/igorjoxa1118/Tokio_night"
repo_dir="$HOME/Tokio_night"

# Подтвердить, что директория репозитория существует, и если она есть, тогда удалить
	if [ -d "$repo_dir" ]; then
		printf "Removing existing dotfiles repository\n"
		rm -rf "$repo_dir"
	fi

# Clona el repositorio
printf "Cloning dotfiles from %s\n" "$repo_url"
git clone --depth=1 "$repo_url" "$repo_dir"

sleep 2
clear