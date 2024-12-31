#!/bin/bash
#set -x

##----------------
#--Colors
##----------------
CRE=$(tput setaf 1)
CYE=$(tput setaf 3)
CGR=$(tput setaf 2)
CBL=$(tput setaf 4)
BLD=$(tput bold)
CNC=$(tput sgr0)

RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
LIGHTBLUE='\033[1;34m'
LIGHTCYAN='\033[1;36m'

##-----------------
#---Vars
##-----------------

paru_url="https://aur.archlinux.org/paru-bin.git"
home_dir=$HOME
current_dir=$(pwd)
ERROR_LOG="$HOME/RiceError.log"

##-----------------
#--Logo
##-----------------

logo_install () {
	echo -en "${PURPLE}                                  
 __ __  ____  ____   ___   _____     ____   ____    __  __  _   ____   ____    ___  _____     ____  ____   _____ ______   ____  _      _     
|  |  ||    ||    \ /   \ / ___/    |    \ /    |  /  ]|  |/ ] /    | /    |  /  _]/ ___/    |    ||    \ / ___/|      | /    || |    | |    
|  |  | |  | |  D  )     (   \_     |  o  )  o  | /  / |  ' / |  o  ||   __| /  [_(   \_      |  | |  _  (   \_ |      ||  o  || |    | |    
|  |  | |  | |    /|  O  |\__  |    |   _/|     |/  /  |    \ |     ||  |  ||    _]\__  |     |  | |  |  |\__  ||_|  |_||     || |___ | |___ 
|  :  | |  | |    \|     |/  \ |    |  |  |  _  /   \_ |     \|  _  ||  |_ ||   [_ /  \ |     |  | |  |  |/  \ |  |  |  |  _  ||     ||     |
 \   /  |  | |  .  \     |\    |    |  |  |  |  \     ||  .  ||  |  ||     ||     |\    |     |  | |  |  |\    |  |  |  |  |  ||     ||     |
  \_/  |____||__|\_|\___/  \___|    |__|  |__|__|\____||__|\_||__|__||___,_||_____| \___|    |____||__|__| \___|  |__|  |__|__||_____||_____|
                                                                                                                                             \n"
    printf ' %s [%s%s %s%s]%s\n\n' "${CRE}" "${CNC}" "${CYE}" "${CNC}" "${CRE}" "${CNC}"
}

########## ---------- Скрипт должен быть запущен от sudo ---------- ##########

if [ "$(id -u)" = 0 ]; then
    echo -e "${LIGHTBLUE}This script MUST NOT be run as root user."
    exit 1
fi

########## ---------- Приветики пистолетики =) ---------- ##########

logo_install
printf '%s%s This script checks to see if you have the necessary requirements, and if not, it will install them.%s\n\n' "${BLD}" "${CRE}" "${CNC}"

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

dependencias=(base-devel alacritty brightnessctl dunst bottom imagemagick \
              libwebp maim mpc neovim ncmpcpp npm pamixer neovim \
              papirus-icon-theme pacman-contrib physlock playerctl python-gobject \
              redshift rust ttf-inconsolata ttf-jetbrains-mono ttf-jetbrains-mono-nerd \
              ttf-joypixels ttf-terminus-nerd ueberzug webp-pixbuf-loader xclip \
              xdo ttf-nerd-fonts-symbols ttf-nerd-fonts-symbols-common \
              ttf-nerd-fonts-symbols-mono yad cmus jgmenu rsync mpv jq git socat mpd polkit-gnome \
              stalonetray kitty lsd ranger micro blueman mousepad ristretto firefox thunar thunar-volman \
              thunar-media-tags-plugin thunar-archive-plugin polybar rofi xdg-user-dirs engrampa bc \
              nitrogen feh picom yt-dlp fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-autosuggestions \
              zsh-history-substring-search starship bluez-utils bluez-tools bluez-plugins bluez-libs bluez \
              zziplib unarj libzip karchive gnome-autoar file-roller \
              cpio arj perl libarchive telegram-desktop code discord gimp blender krita kdenlive kodi \
              kodi-addon-inputstream-adaptive kodi-dev kodi-eventclients kodi-platform p8-platform vde2 xorg-xdpyinfo xorg-xwininfo \
              xorg-xkill xorg-xprop xorg-xrandr xorg-xsetroot xdotool bzip2 gzip lrzip lz4 lzip lzop xz zstd p7zip zip unzip unrar \
              yazi unarchiver xarchiver qt6-svg qt6-declarative qt5-quickcontrols2 qt5-graphicaleffects ffmpeg poppler fd ripgrep zoxide)



dependencias_paru=(cava tor-browser-bin ymuse-git zscroll-git eww-git musnify-mpd gnome-icon-theme catppuccin-cursors-mocha ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
                  zenity-gtk3 i3lock-color gdown pamac-aur kazam kodi-addon-pvr-iptvsimple hypnotix)

is_installed() {
  pacman -Qi "$1" &> /dev/null
  return $?
}

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

########## ---------- Установка paru---------- ##########
logo_paru () {
	echo -en "${ORANGE}                                  
 ____   ____  ____  __ __      ____  ____   _____ ______   ____  _      _     
|    \ /    ||    \|  |  |    |    ||    \ / ___/|      | /    || |    | |    
|  o  )  o  ||  D  )  |  |     |  | |  _  (   \_ |      ||  o  || |    | |    
|   _/|     ||    /|  |  |     |  | |  |  |\__  ||_|  |_||     || |___ | |___ 
|  |  |  _  ||    \|  :  |     |  | |  |  |/  \ |  |  |  |  _  ||     ||     |
|  |  |  |  ||  .  \     |     |  | |  |  |\    |  |  |  |  |  ||     ||     |
|__|  |__|__||__|\_|\__,_|    |____||__|__| \___|  |__|  |__|__||_____||_____|
                                                                              \n"
    printf ' %s [%s%s %s%s]%s\n\n' "${CRE}" "${CNC}" "${CYE}" "${CNC}" "${CRE}" "${CNC}"
}
logo_paru

clone_paru() {
# Installing Paru
if command -v paru >/dev/null 2>&1; then
    printf "%s%sParu is already installed%s\n" "${BLD}" "${CGR}" "${CNC}"
else
    printf "%s%sInstalling paru%s\n" "${BLD}" "${CBL}" "${CNC}"
    {
        cd "$HOME" || exit
        git clone $paru_url
        cd "$HOME"/paru-bin || exit
        makepkg -si --noconfirm
        } || {
        printf "\n%s%sFailed to install Paru. You may need to install it manually%s\n" "${BLD}" "${CRE}" "${CNC}"
    }
fi
}

while true; do
	read -rp "Do you want paru? [y/N]: " yn
		case $yn in
			[Yy]* ) clone_paru && break;;
			[Nn]* ) break;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

########## ---------- Установка пакетов AUR---------- ##########

is_installed_paru() {
  paru -Qi "$1" &> /dev/null
  return $?
}

printf "%s%sChecking for required packages...%s\n" "${BLD}" "${CBL}" "${CNC}"
for pkges_paru in "${dependencias_paru[@]}"
do
  if ! is_installed_paru "$pkges_paru"; then
    paru -S "$pkges_paru" --noconfirm
    printf "\n"
  else
    printf '%s%s is already installed on your system!%s\n' "${CGR}" "$pkges_paru" "${CNC}"
    sleep 1
  fi
done
sleep 2
clear

logo_all_done () {
	echo -en "${GREEN}                                  
  ____  _      _          ____ _____     ___     ___   ____     ___  __ 
 /    || |    | |        |    / ___/    |   \   /   \ |    \   /  _]|  |
|  o  || |    | |         |  (   \_     |    \ |     ||  _  | /  [_ |  |
|     || |___ | |___      |  |\__  |    |  D  ||  O  ||  |  ||    _]|__|
|  _  ||     ||     |     |  |/  \ |    |     ||     ||  |  ||   [_  __ 
|  |  ||     ||     |     |  |\    |    |     ||     ||  |  ||     ||  |
|__|__||_____||_____|    |____|\___|    |_____| \___/ |__|__||_____||__|
                                                                        \n"
    printf ' %s [%s%s %s%s]%s\n\n' "${CRE}" "${CNC}" "${CYE}" "${CNC}" "${CRE}" "${CNC}"
}
logo_all_done
sleep 2
clear

########## ---------- Резервная копия файлов и каталогов ---------- ##########
backup_folder=~/.Backup_files
  echo -e "${CYAN}Backup files will be stored in .Backup_files"
  rsync -aAEHSXxr --exclude=".cache/mozilla/*" ~/.[^.]* $backup_folder
  echo -e "${ORANGE}Done!!"


for del in polybar rofi picom.conf; do
   rm -rf ~/.config/$del
   echo -e "${YELLOW}$del deleted"
done
sleep 2

########## ---------- Установка dot-файлов ---------- ##########
func_install_dots() {
cp -rf "$current_dir"/user/.* "$home_dir"
if [ ! -d /usr/share/grub/themes/catppuccin-mocha-grub-theme ]; then
sudo cp -rf "$current_dir"/grub_themes/catppuccin-mocha-grub-theme /usr/share/grub/themes/
fi
echo -e "${GRE}Copy dots succesfully!"

  if [ -d "$current_dir"/pkgs_virOS ]; then
    echo "${CYAN}Folder exist"
  else
    cd "$current_dir || exit" || exit
    if [ ! -d "$current_dir/pkgs_virOS" ]; then
    gdown --folder 19SlCmblUJts_I5dlAwd2C3tq7q2-wLbS
    echo -e "${GRE}Packages in system!"
    sudo rm -rf /usr/share/icons/*
    sudo pacman -U "$current_dir"/pkgs_virOS/*.zst --noconfirm
    fi
  fi
}

##-------------------
#--Install bin files
##-------------------
sudo cp rf "$current_dir"/user/.bin/virlock /usr/bin
### --- Завершение копирования dot-файлов --- ###
func_install_dots
sleep 2

### --- Сканирование шрифтов
fc-cache -fv
### --- Делает Thunar двухпанельным
xfconf-query -c thunar -p /misc-open-new-windows-in-split-view -n -t bool -s true
clear

### --- Установка SDDM --- ###
logo "Install SDDM"

if [ -f /usr/bin/lightdm ]; then
   sudo systemctl disable lightdm.service
   sudo pacman -Rdd lightdm lightdm-gtk-greeter --noconfirm
fi

if [ -d /etc/sddm.conf.d/ ]; then
   sudo cp -rf "$current_dir"/sddm/sddm.conf.d /etc/
   sudo cp -rf "$current_dir"/sddm/catppuccin-mocha /usr/share/sddm/themes
   sudo systemctl enable sddm.service
   echo -e "${LIGHTCYAN}Done!"
 else 
   sudo pacman -S sddm --noconfirm
   sudo cp -rf "$current_dir"/sddm/sddm.conf.d /etc/
   sudo cp -rf "$current_dir"/sddm/catppuccin-mocha /usr/share/sddm/themes
   sudo systemctl enable sddm.service
   echo -e "${LIGHTCYAN}Done!"
fi

if [ -d /etc/lightdm ]; then
  sudo rm -rf /etc/lightdm
fi
sleep 2

##-------------------
#--Grub themes apply
##-------------------
GRUB_THEME_DIR="/usr/share/grub/themes"
grub_theme="catppuccin-mocha-grub-theme"
    if grep "GRUB_THEME=" /etc/default/grub cmd >/dev/null; then
      #Replace GRUB_THEME
      sudo sed -i "s|.*GRUB_THEME=.*|GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"|" /etc/default/grub
      sudo grub-mkconfig -o /boot/grub/grub.cfg
    else
      #Append GRUB_THEME
      echo "GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"" | sudo tee /etc/default/grub
      sudo grub-mkconfig -o /boot/grub/grub.cfg
    fi

### --- Установка темы и конфигов Firefox --- ###
copy_ff_func() {
  cp -R "$current_dir"/firefox/FoxThemes/* ~/.mozilla/firefox/"$PROFPATH"
  echo -e "${GREEN}Firefox theme installed"
  sleep 2
}

firefox_profiles() {
if [[ $(grep '\[Profile[^0]\]' "$HOME"/.mozilla/firefox/profiles.ini) ]]
then PROFPATH=$(grep -E '^\[Profile|^Path|^Default' "$HOME"/.mozilla/firefox/profiles.ini | grep -1 '^Default=1' | grep '^Path' | cut -c6-)
else PROFPATH=$(grep 'Path=' "$HOME"/.mozilla/firefox/profiles.ini | sed 's/^Path=//')
fi
}

if [ -z "$PROFPATH" ]; then
   copy_ff_func
else
   echo -e "${RED}Firefox themes not installed"
   sleep 2
   exit 1
fi
sleep 2

#### ------- Проверка видеокарты. Если карта отсутствует, то модули на polybar будут другие --- ###
  scrDir="$(dirname "$(realpath "$0")")"
    readarray -t dGPU < <(lspci -k | grep -E "(VGA|3D)" | awk -F ': ' '{print $NF}')
    if [ "${1}" == "--verbose" ]; then
        for indx in "${!dGPU[@]}"; do
            echo -e "\033[0;32m[gpu$indx]\033[0m detected // ${dGPU[indx]}"
        done
        return 0
    fi
    if [ "${1}" == "--drivers" ]; then
        while read -r -d ' ' nvcode ; do
            awk -F '|' -v nvc="${nvcode}" 'substr(nvc,1,length($3)) == $3 {split(FILENAME,driver,"/"); print driver[length(driver)],"\nnvidia-utils"}' "${scrDir}"/.nvidia/nvidia*dkms
        done <<< "${dGPU[@]}"
        return 0
    fi
    if grep -iq nvidia <<< "${dGPU[@]}"; then
        rm -rf "$home_dir/.config/i3/rices/catppuccin-mocha/config.ini"
        cd "$current_dir"/polybar_rices/nvidia || exit
        cp -R config.ini "$home_dir/.config/i3/rices/catppuccin-mocha/"
        echo -e "${ORANGE}Nvidia card found!"
    else
        rm -rf "$home_dir/.config/i3/rices/catppuccin-mocha/config.ini"
        cd "$current_dir"/polybar_rices/not_nvidia || exit
        cp -R config.ini "$home_dir/.config/i3/rices/catppuccin-mocha/"
        echo -e "${CYAN}Nvidia card NOT found!"
    fi
sleep 2

### --- Добавление пользователя в группы вирутальных машин. --- ###
echo -e "${ORANGE}Enabling Groups"
    sudo usermod -a -G libvirt "$(whoami)"
    newgrp libvirt
echo -e "${ORANGE}Done!"
sleep 2

	if systemctl is-enabled --quiet mpd.service; then
        printf "%s%sDisabling and stopping the global mpd service%s\n" "${BLD}" "${CBL}" "${CNC}"

        if sudo systemctl disable --now mpd.service >/dev/null 2> >(tee -a "$ERROR_LOG"); then
            sleep 1
            printf "\n%s[%sOK%s%s]%s Global MPD service disabled successfully\n\n" \
                   "${BLD}" "${CGR}" "${CNC}" "${BLD}" "${CNC}"
        else
            sleep 1
            printf "%s[%sError%s%s] Please check %sRiceError.log%s for details\n\n" \
               "${BLD}" "${CRE}" "${CNC}" "${BLD}" "${CYE}" "${CNC}"
            log_error "Failed to disable global MPD service"
		fi
	fi

    printf "%s%sEnabling and starting the user-level mpd service%s\n\n" "${BLD}" "${CBL}" "${CNC}"

    if systemctl --user enable --now mpd.service >/dev/null 2> >(tee -a "$ERROR_LOG"); then
        sleep 1
        printf "%s[%sOK%s%s]%s User-level MPD service enabled successfully\n\n" \
               "${BLD}" "${CGR}" "${CNC}" "${BLD}" "${CNC}"
    else
        sleep 1
        printf "%s[%sError%s%s] Please check %sRiceError.log%s for details\n\n" \
               "${BLD}" "${CRE}" "${CNC}" "${BLD}" "${CYE}" "${CNC}"
        log_error "Failed to enable user-level MPD service"
    fi
sleep 2

########## --------- Замена шелла на zsh ---------- ##########

	if [[ $SHELL != "/usr/bin/zsh" ]]; then
        printf "%s%sChanging your shell to zsh...%s\n\n" "${BLD}" "${CYE}" "${CNC}"

        if chsh -s /usr/bin/zsh 2> >(tee -a "$ERROR_LOG"); then
            printf "\n%s[%sOK%s%s] Shell changed to zsh successfully!%s\n\n" "${BLD}" "${CGR}" "${CNC}" "${BLD}" "${CNC}"
        else
            printf "%s%sError changing your shell to zsh. Please check %sRiceError.log%s for details%s\n\n" \
                   "${BLD}" "${CRE}" "${CYE}" "${CRE}" "${CNC}"
            log_error "Failed to change shell to zsh"
        fi
    else
        printf "%s%sYour shell is already zsh%s\n\n" "${BLD}" "${CGR}" "${CNC}"
    fi
sleep 2

########## --------- Выход ---------- ##########

printf "%sThe installation is complete, you %sneed%s to restart your machine.%s\n\n" "${BLD}" "${CBL}" "${CNC}" "${CNC}"

	while true; do
		read -rp " Reboot now? [y/N]: " yn
		case $yn in
			[Yy]* )
				printf "\n%s%sRebooting now...%s\n" "${BLD}" "${CGR}" "${CNC}"
				sleep 3
				reboot
				break
				;;
			[Nn]* )
				printf "\n%s%sOK, remember to restart later!%s\n\n" "${BLD}" "${CYE}" "${CNC}"
				break
				;;
			* )
				printf "\n%s%sPlease answer yes or no.%s\n\n" "${BLD}" "${CRE}" "${CNC}"
				;;
		esac
	done