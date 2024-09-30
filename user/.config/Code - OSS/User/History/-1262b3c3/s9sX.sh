#!/bin/bash
#set -x

CRE=$(tput setaf 1)
CYE=$(tput setaf 3)
CGR=$(tput setaf 2)
CBL=$(tput setaf 4)
BLD=$(tput bold)
CNC=$(tput sgr0)

NOCOLOR='\033[0m'
RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
LIGHTGRAY='\033[0;37m'
DARKGRAY='\033[1;30m'
LIGHTRED='\033[1;31m'
LIGHTGREEN='\033[1;32m'
YELLOW='\033[1;33m'
LIGHTBLUE='\033[1;34m'
LIGHTPURPLE='\033[1;35m'
LIGHTCYAN='\033[1;36m'
WHITE='\033[1;37m'

pwd=$(pwd)
old_folder=~/.old_files
backup_part=~/vir0id/Загрузки/USB_BACKUP_I3WM/
date=$(date +%Y%m%d-%H%M%S)
yay_git="https://aur.archlinux.org/yay.git"


user=$(whoami)

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

                                          ########## ---------- Скрипт НЕ должен быть запущен от sudo ---------- ##########

if [ "$(id -u)" = 0 ]; then
    echo -e "${LIGHTBLUE}This script MUST NOT be run as root user."
    exit 1
fi

                                          ########## ---------- Приветики пистолетики =) ---------- ##########

logo "Welcome!"
printf '%s%s Установка начинается!=)' "${BLD}" "${CRE}" "${CNC}"

while true; do
	read -rp "Do you wish to continue? [y/N]: " yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

                                          ######### -------------- Зависимости ------------------########

dependencias=(base-devel yad cmus jgmenu rsync mpv jq git socat mpd polkit-gnome stalonetray kitty lsd ranger retroarch\
              micro blueman mousepad ristretto firefox thunar thunar-volman thunar-media-tags-plugin thunar-archive-plugin \
              caja polybar rofi dunst xdg-user-dirs engrampa bc nitrogen picom yt-dlp zsh-history-substring-search \
              fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-autosuggestions starship bluez-utils unarchiver p7zip \
              bluez-tools bluez-plugins bluez-libs bluez blueman zziplib zip xarchiver unzip unarj libzip karchive \
              gnome-autoar file-roller engrampa cpio arj perl libarchive telegram-desktop code discord gimp blender krita ristretto \
              kdenlive kodi kodi-addon-inputstream-adaptive kodi-dev kodi-eventclients kodi-platform p8-platform vde2)

dependencias_yay=(cava zscroll-git ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
                  zenity-gtk3 eww musikcube i3lock-color pamac-aur kazam kodi-addon-pvr-iptvsimple hypnotix)


                                          ########## ---------- Установка пакетов из стандартных репозиториев pacman ---------- ##########

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
sleep 2
clear

                                          ########## ---------- Установка пакетов из AUR---------- ##########

is_installed_yay() {
  yay -Qi "$1" &> /dev/null
  return $?
}

printf "%s%sChecking for required packages...%s\n" "${BLD}" "${CBL}" "${CNC}"
for pkges_yay in "${dependencias_yay[@]}"
do
  if ! is_installed_yay "$pkges_yay"; then
    yay -S "$pkges_yay" --noconfirm
    printf "\n"
  else
    printf '%s%s is already installed on your system!%s\n' "${CGR}" "$pkges_yay" "${CNC}"
    sleep 1
  fi
done
sleep 2
clear

                                          ########## ---------- Резервное копирование и удаление старых файлов ---------- ##########

logo "Remove and backup restore files"
echo -e "${CYAN}Backup files will be stored in .old_files"
rsync -aAEHSXxr --exclude=".cache/mozilla/*" ~/.[^.]* $old_folder
clear
echo -e "${CYAN}Done!"
sleep 2
clear

echo -e "${CYAN}Remove old files"
rm -rf ~/.*
clear
echo -e "${CYAN}Done!"
sleep 2
clear

echo -e "${CYAN}Install skel..."
rsync -aAEHSXxr ~/$backup_part.[^.]* ~/
clear
echo -e "${CYAN}Done!"
sleep 2
clear

                                          ########## --------- Замена шелла на zsh ---------- ##########

shell_change() {
  logo "Changing default shell to zsh"
	if [[ $SHELL != "/usr/bin/zsh" ]]; then
		echo -e "${ORANGE}Changing your shell to zsh. Your root password is needed."
		# Переключиться на zsh
		chsh -s /usr/bin/zsh
		echo -e "${LIGHTBLUE}Shell changed to zsh. Reboot."
        sleep 2
        reboot
	else
		echo -e "${CYAN}Your shell is already zsh! Installation finished, now reboot"
	fi
}
if shell_change