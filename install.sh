#!/bin/bash
#set -x

##----------------
#--Colors
##----------------
# CRE=$(tput setaf 1)
# CYE=$(tput setaf 3)
# CGR=$(tput setaf 2)
# CBL=$(tput setaf 4)
# BLD=$(tput bold)
# CNC=$(tput sgr0)

RED='\033[0;31m'
GREEN='\033[0;32m'
ORANGE='\033[0;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
LIGHTBLUE='\033[1;34m'
LIGHTCYAN='\033[1;36m'
ENDCOLOR="\e[0m"

##-----------------
#---Vars
##-----------------

backup_folder=~/.Backup_files
ERROR_LOG="$HOME/RiceError.log"

##-----------------
#--Logo
##-----------------

logo_install () {
	echo -en "${PURPLE}                                  
██    ██ ██ ██████   ██████  ██ ██████      ██████   ██████  ████████ ███████ 
██    ██ ██ ██   ██ ██  ████ ██ ██   ██     ██   ██ ██    ██    ██    ██      
██    ██ ██ ██████  ██ ██ ██ ██ ██   ██     ██   ██ ██    ██    ██    ███████ 
 ██  ██  ██ ██   ██ ████  ██ ██ ██   ██     ██   ██ ██    ██    ██         ██ 
  ████   ██ ██   ██  ██████  ██ ██████      ██████   ██████     ██    ███████ 
                                                                              
                                                                              ${ENDCOLOR}\n"
}

########## ---------- Скрипт должен быть запущен от sudo ---------- ##########

if [ "$(id -u)" = 0 ]; then
    echo -e "${LIGHTBLUE}This script MUST NOT be run as root user.${ENDCOLOR}"
    exit 1
fi

home_dir=$HOME
current_dir=$(pwd)

if [ ! -f /usr/bin/firefox ]; then
     sudo pacman -S firefox --noconfirm &> /dev/null
     echo -e "${GREEN}Start Firefox manualy! Its important!${ENDCOLOR}"
     exit 1
fi

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$ERROR_LOG"
}

is_installed() {
    pacman -Qq "$1" &> /dev/null
}

########## ---------- Приветики пистолетики =) ---------- ##########

logo_install
echo -e "${YELLOW}This script checks to see if you have the necessary requirements, and if not, it will install them.!${ENDCOLOR}"

while true; do
	read -rp "Do you wish to continue? [y/N]: " yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit;;
			* ) echo "Please answer yes or no.";;
		esac
    done
clear


if [ -f /usr/bin/i3lock ]; then 
  sudo pacman -R i3lock --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
fi

if [ -f /usr/bin/zenity ]; then
  sudo pacman -R zenity --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
fi

######### -------------- Зависимости ------------------########

dependencias=(base-devel alacritty brightnessctl dunst bottom imagemagick \
              libwebp maim mpc neovim ncmpcpp npm pamixer neovim \
              papirus-icon-theme pacman-contrib physlock playerctl python-gobject \
              redshift rust ttf-inconsolata ttf-jetbrains-mono ttf-jetbrains-mono-nerd \
              ttf-joypixels ttf-terminus-nerd ueberzug webp-pixbuf-loader xclip \
              xdo ttf-nerd-fonts-symbols ttf-nerd-fonts-symbols-common \
              ttf-nerd-fonts-symbols-mono yad cmus rsync mpv jq git socat mpd polkit-gnome \
              stalonetray kitty lsd ranger micro blueman mousepad ristretto firefox thunar thunar-volman \
              thunar-media-tags-plugin thunar-archive-plugin polybar rofi xdg-user-dirs engrampa bc \
              nitrogen feh picom yt-dlp fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-autosuggestions \
              zsh-history-substring-search starship bluez-utils bluez-tools bluez-plugins bluez-libs bluez \
              zziplib unarj libzip karchive gnome-autoar file-roller \
              cpio arj perl libarchive telegram-desktop code discord gimp blender krita kdenlive kodi \
              kodi-addon-inputstream-adaptive kodi-dev kodi-eventclients kodi-platform p8-platform vde2 xorg-xdpyinfo xorg-xwininfo \
              xorg-xkill xorg-xprop xorg-xrandr xorg-xsetroot xdotool bzip2 gzip lrzip lz4 lzip lzop xz zstd p7zip zip unzip unrar \
              yazi unarchiver xarchiver qt6-svg qt6-declarative qt5-quickcontrols2 qt5-graphicaleffects ffmpeg poppler fd ripgrep zoxide)




########## ---------- Установка пакетов из стандартных репозиториев pacman ---------- ##########
echo -e "${YELLOW}Checking for required packages...!${ENDCOLOR}"
for pkges in "${dependencias[@]}"
do
  if ! is_installed "$pkges"; then
    if sudo pacman -S "$pkges" --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG"); then
    echo -e "${YELLOW}$pkges${ENDCOLOR}${LIGHTBLUE} has been installed succesfully.${ENDCOLOR}"
  else
                echo -e "${YELLOW}$pkges${ENDCOLOR}${RED} has NOT been installed. See ${YELLOW}RiceError.log${ENDCOLOR}"
                log_error "Failed to install package: $pkges"
            fi
            sleep 1
        else
            echo -e "${YELLOW}$pkges${GREEN} is already installed on your system!${ENDCOLOR}"
            sleep 1
        fi
    done
sleep 3
clear

# Verifies if the archive user-dirs.dirs doesn't exist in ~/.config
if [ ! -e "$HOME/.config/user-dirs.dirs" ]; then
    xdg-user-dirs-update
fi

########## ---------- Установка paru---------- ##########
logo_paru () {
	echo -en "${ORANGE}                                  
██████   █████  ██████  ██    ██     ██ ███    ██ ███████ ████████  █████  ██      ██      
██   ██ ██   ██ ██   ██ ██    ██     ██ ████   ██ ██         ██    ██   ██ ██      ██      
██████  ███████ ██████  ██    ██     ██ ██ ██  ██ ███████    ██    ███████ ██      ██      
██      ██   ██ ██   ██ ██    ██     ██ ██  ██ ██      ██    ██    ██   ██ ██      ██      
██      ██   ██ ██   ██  ██████      ██ ██   ████ ███████    ██    ██   ██ ███████ ███████ 
                                                                                           
                                                                                           ${ENDCOLOR}\n"
}
logo_paru

if command -v paru >/dev/null 2>&1; then
    echo -e "${YELLOW}Paru is already installed!${ENDCOLOR}"
else
    echo -e "${YELLOW}Installing paru!${ENDCOLOR}"
    {
        cd "$HOME" || exit
        git clone https://aur.archlinux.org/paru-bin.git
        cd paru-bin || exit
        makepkg -si --noconfirm 
        } || {
        echo -e "${RED}Failed to install Paru. You may need to install it manually!${ENDCOLOR}"
    }
fi
sleep 3
clear

if [ ! -f /usr/bin/paru ]; then
echo -e "${RED}Paru not installed! Exit script!${ENDCOLOR}" 
exit 1
fi

########## ---------- Установка пакетов AUR---------- ##########

dependencias_paru=(cava tor-browser-bin ymuse-git zscroll-git eww-git musnify-mpd gnome-icon-theme \
                   catppuccin-cursors-mocha ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
                   i3lock-color gdown kazam kodi-addon-pvr-iptvsimple hypnotix)

echo -e "${YELLOW}Checking for required custom packages...!${ENDCOLOR}"
for aur_package in "${dependencias_paru[@]}"; do
    if ! is_installed "$aur_package"; then
        if paru -S --skipreview --noconfirm "$aur_package" 2> >(tee -a "$ERROR_LOG"); then
            echo -e "${YELLOW}$aur_package${ENDCOLOR}${LIGHTBLUE} has been installed succesfully.${ENDCOLOR}"
        else
            echo -e "${YELLOW}$aur_package${ENDCOLOR}${RED} has NOT been installed. See ${YELLOW}RiceError.log${ENDCOLOR}"
            log_error "Failed to install package: $aur_package"
        fi
        sleep 1
    else
        echo -e "${YELLOW} $aur_package ${GREEN} is already installed on your system!${ENDCOLOR}"
        sleep 1
    fi
done
sleep 3
clear


logo_all_done () {
	echo -en "${GREEN}                                  
 █████  ██      ██          ██ ███████     ██████   ██████  ███    ██ ███████ ██ 
██   ██ ██      ██          ██ ██          ██   ██ ██    ██ ████   ██ ██      ██ 
███████ ██      ██          ██ ███████     ██   ██ ██    ██ ██ ██  ██ █████   ██ 
██   ██ ██      ██          ██      ██     ██   ██ ██    ██ ██  ██ ██ ██         
██   ██ ███████ ███████     ██ ███████     ██████   ██████  ██   ████ ███████ ██ 
                                                                                 
                                                                                 ${ENDCOLOR}\n"
}
logo_all_done
sleep 2
clear

########## ---------- Резервная копия файлов и каталогов ---------- ##########
logo_backup_files () {
	echo -en "${GREEN}                                  
██████   █████   ██████ ██   ██ ██    ██ ██████  
██   ██ ██   ██ ██      ██  ██  ██    ██ ██   ██ 
██████  ███████ ██      █████   ██    ██ ██████  
██   ██ ██   ██ ██      ██  ██  ██    ██ ██      
██████  ██   ██  ██████ ██   ██  ██████  ██      
                                                 
                                                 ${ENDCOLOR}\n"
}
logo_backup_files

  echo -e "${CYAN}Backup files will be stored in .Backup_files${ENDCOLOR}"
  sudo rsync -aAEHSXxr --delete --exclude=".cache/mozilla/*" ~/.[^.]* $backup_folder
  echo -e "${ORANGE}Done!!${ENDCOLOR}"


for del in polybar rofi picom.conf; do
   rm -rf ~/.config/$del
done
sleep 2
clear

########## ---------- Установка dot-файлов ---------- ##########
logo_install_dots () {
	echo -en "${GREEN}                                  
██ ███    ██ ███████ ████████  █████  ██      ██          ██████   ██████  ████████ ███████ ██ ██      ███████ ███████ 
██ ████   ██ ██         ██    ██   ██ ██      ██          ██   ██ ██    ██    ██    ██      ██ ██      ██      ██      
██ ██ ██  ██ ███████    ██    ███████ ██      ██          ██   ██ ██    ██    ██    █████   ██ ██      █████   ███████ 
██ ██  ██ ██      ██    ██    ██   ██ ██      ██          ██   ██ ██    ██    ██    ██      ██ ██      ██           ██ 
██ ██   ████ ███████    ██    ██   ██ ███████ ███████     ██████   ██████     ██    ██      ██ ███████ ███████ ███████ 
                                                                                                                       
                                                                                                                       ${ENDCOLOR}\n"
}
logo_install_dots

func_install_dots() {
    cp -rf "$current_dir"/user/.* "$home_dir"
if [ ! -d /usr/share/grub/themes/catppuccin-mocha-grub-theme ]; then
    sudo cp -rf "$current_dir"/grub_themes/catppuccin-mocha-grub-theme /usr/share/grub/themes/ >/dev/null 2> >(tee -a "$ERROR_LOG")
fi

if [ -d "$current_dir"/pkgs_virOS ]; then
    echo -e "${CYAN}Folder exist${ENDCOLOR}"
else
    cd "$current_dir" || exit
  if [ ! -d "$current_dir/pkgs_virOS" ]; then
    gdown --folder 19SlCmblUJts_I5dlAwd2C3tq7q2-wLbS
    echo -e "${GRE}Install pkgs in system!${ENDCOLOR}"
    sudo rm -rf /usr/share/icons/* 
    sudo pacman -U "$current_dir"/pkgs_virOS/*.zst --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
  fi
fi
echo -e "${GRE}Copy dots succesfully!${ENDCOLOR}"
}

##-------------------
#--Install bin files
##-------------------
sudo cp -rf "$current_dir"/user/.bin/virlock /usr/bin
### --- Завершение копирования dot-файлов --- ###
func_install_dots
sleep 2

### --- Сканирование шрифтов
fc-cache -rv >/dev/null 2>&1
### --- Делает Thunar двухпанельным
xfconf-query -c thunar -p /misc-open-new-windows-in-split-view -n -t bool -s true
clear

### --- Установка SDDM --- ###
logo_install_sddm () {
	echo -en "${GREEN}                                  
███████ ██████  ██████  ███    ███ 
██      ██   ██ ██   ██ ████  ████ 
███████ ██   ██ ██   ██ ██ ████ ██ 
     ██ ██   ██ ██   ██ ██  ██  ██ 
███████ ██████  ██████  ██      ██ 
                                   
                                   ${ENDCOLOR}\n"
}
logo_install_sddm

if [ -f /usr/bin/lightdm ]; then
   sudo systemctl disable lightdm.service >/dev/null 2> >(tee -a "$ERROR_LOG")
   sudo pacman -Rdd lightdm lightdm-gtk-greeter --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
fi

if [ -d /etc/sddm.conf.d/ ]; then
    sudo cp -rf "$current_dir"/sddm/sddm.conf.d /etc/
    sudo cp -rf "$current_dir"/sddm/catppuccin-mocha /usr/share/sddm/themes
    sudo systemctl enable sddm.service >/dev/null 2> >(tee -a "$ERROR_LOG")
    echo -e "${LIGHTCYAN}Done!${ENDCOLOR}"
 else 
    sudo pacman -S sddm --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
    sudo cp -rf "$current_dir"/sddm/sddm.conf.d /etc/ >/dev/null 2> >(tee -a "$ERROR_LOG")
    sudo cp -rf "$current_dir"/sddm/catppuccin-mocha /usr/share/sddm/themes >/dev/null 2> >(tee -a "$ERROR_LOG")
    sudo systemctl enable sddm.service >/dev/null 2> >(tee -a "$ERROR_LOG")
    echo -e "${LIGHTCYAN}Done!${ENDCOLOR}"
fi

if [ -d /etc/lightdm ]; then
  sudo rm -rf /etc/lightdm
fi
sleep 3
clear

##-------------------
#--Grub themes apply
##-------------------
logo_install_grub () {
	echo -en "${GREEN}                                  
 ██████  ██████  ██    ██ ██████  
██       ██   ██ ██    ██ ██   ██ 
██   ███ ██████  ██    ██ ██████  
██    ██ ██   ██ ██    ██ ██   ██ 
 ██████  ██   ██  ██████  ██████  
                                  
                                  ${ENDCOLOR}\n"
}
logo_install_grub

install_grub_theme() {
GRUB_THEME_DIR="/usr/share/grub/themes"
grub_theme="catppuccin-mocha-grub-theme"

if [ ! -d "$GRUB_THEME_DIR"/"$grub_theme" ]; then
    sudo cp -rf "$current_dir"/grub_themes/"$grub_theme" /usr/share/grub/themes/
fi

  if [ -f /etc/default/grub ]; then
      #Replace GRUB_THEME
      sudo sed -i "s|.*GRUB_THEME=.*|GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"|" /etc/default/grub >/dev/null 2> >(tee -a "$ERROR_LOG")
      sudo grub-mkconfig -o /boot/grub/grub.cfg >/dev/null 2> >(tee -a "$ERROR_LOG")
      echo -e "${LIGHTCYAN}Done!${ENDCOLOR}"
  else
      #Append GRUB_THEME
      echo "GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"" | sudo tee /etc/default/grub
      sudo grub-mkconfig -o /boot/grub/grub.cfg >/dev/null 2> >(tee -a "$ERROR_LOG")
      echo -e "${LIGHTCYAN}Done!${ENDCOLOR}"
  fi
}
install_grub_theme
sleep 3
clear

### --- Установка темы и конфигов Firefox --- ###
logo_install_firefox () {
	echo -en "${GREEN}                                  
███████ ██ ██████  ███████ ███████  ██████  ██   ██ 
██      ██ ██   ██ ██      ██      ██    ██  ██ ██  
█████   ██ ██████  █████   █████   ██    ██   ███   
██      ██ ██   ██ ██      ██      ██    ██  ██ ██  
██      ██ ██   ██ ███████ ██       ██████  ██   ██ 
                                                    
                                                    ${ENDCOLOR}\n"
}
logo_install_firefox

firefox_profiles() {
if [[ $(grep '\[Profile[^0]\]' ~/.mozilla/firefox/profiles.ini) ]]; then 
    PROFPATH_0=$(grep -A 10 "\[Profile0\]" ~/.mozilla/firefox/profiles.ini | sed '1d'| grep -m 1 -B 10 "\["| grep "Path=" | sed -e 's/Path=//')
elif [[ $(grep '\[Profile[^1]\]' ~/.mozilla/firefox/profiles.ini) ]]; then 
    PROFPATH_1=$(grep -A 10 "\[Profile1\]" ~/.mozilla/firefox/profiles.ini | sed '1d'| grep -m 1 -B 10 "\["| grep "Path=" | sed -e 's/Path=//')
fi
}
firefox_profiles

copy_firefox_theme() {
  if [ -d ~/.mozilla/firefox/"$PROFPATH_0" ]; then
    cp -R "$current_dir"/firefox/FoxThemes/* ~/.mozilla/firefox/"$PROFPATH_0"
    echo -e "${GREEN}Firefox theme installed in ${ENDCOLOR}${YELLOW}""$PROFPATH_0""${ENDCOLOR}"
  elif [ -d ~/.mozilla/firefox/"$PROFPATH_1" ]; then
    cp -R "$current_dir"/firefox/FoxThemes/* ~/.mozilla/firefox/"$PROFPATH_1"
    echo -e "${GREEN}Firefox theme installed in ${ENDCOLOR}${YELLOW}""$PROFPATH_1""${ENDCOLOR}" 
  else
    echo -e "${YELLOW}Firefox theme${ENDCOLOR}${RED} has NOT been installed! Install manualy!${ENDCOLOR}"
  fi

  if [ -d ~/.mozilla/firefox/"$PROFPATH_0"/extensions ]; then
    cp -R "$current_dir"/firefox/extensions/* ~/.mozilla/firefox/"$PROFPATH_0"/extensions
    echo -e "${GREEN}Firefox extentions installed in ${ENDCOLOR}${YELLOW}""$PROFPATH_0""${ENDCOLOR}"
  elif [ -d ~/.mozilla/firefox/"$PROFPATH_1"/extensions ]; then
    cp -R "$current_dir"/firefox/extensions/* ~/.mozilla/firefox/"$PROFPATH_1"/extensions
    echo -e "${GREEN}Firefox extentions installed in ${ENDCOLOR}${YELLOW}""$PROFPATH_1""${ENDCOLOR}"
  else
    echo -e "${YELLOW}Firefox extentions${ENDCOLOR}${RED} has NOT been installed! Install manualy!${ENDCOLOR}"
  fi
}


if [ -z "$PROFPATH" ]; then
   copy_firefox_theme
fi
sleep 3
clear

#### ------- Проверка видеокарты. Если карта отсутствует, то модули на polybar будут другие --- ###
logo_install_nvidia () {
	echo -en "${GREEN}                                  
███    ██ ██    ██ ██ ██████  ██  █████  
████   ██ ██    ██ ██ ██   ██ ██ ██   ██ 
██ ██  ██ ██    ██ ██ ██   ██ ██ ███████ 
██  ██ ██  ██  ██  ██ ██   ██ ██ ██   ██ 
██   ████   ████   ██ ██████  ██ ██   ██ 
                                         
                                         ${ENDCOLOR}\n"
}
logo_install_nvidia

  scrDir="$(dirname "$(realpath "$0")")"
    readarray -t dGPU < <(lspci -k | grep -E "(VGA|3D)" | awk -F ': ' '{print $NF}')
    if [ "${1}" == "--verbose" ]; then
        for indx in "${!dGPU[@]}"; do
            echo "[gpu$indx]detected // ${dGPU[indx]}"
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
        echo -e "${ORANGE}Nvidia card found!${ENDCOLOR}"
    else
        rm -rf "$home_dir/.config/i3/rices/catppuccin-mocha/config.ini"
        cd "$current_dir"/polybar_rices/not_nvidia || exit
        cp -R config.ini "$home_dir/.config/i3/rices/catppuccin-mocha/"
        echo -e "${CYAN}Nvidia card NOT found!${ENDCOLOR}"
    fi
sleep 3
clear

### --- Добавление пользователя в группы вирутальных машин. --- ###
logo_install_mdp_libvirt () {
	echo -en "${GREEN}                                  
███    ███ ██████  ██████         ██        ██      ██ ██████  ██    ██ ██ ██████  ████████ 
████  ████ ██   ██ ██   ██        ██        ██      ██ ██   ██ ██    ██ ██ ██   ██    ██    
██ ████ ██ ██████  ██   ██     ████████     ██      ██ ██████  ██    ██ ██ ██████     ██    
██  ██  ██ ██      ██   ██     ██  ██       ██      ██ ██   ██  ██  ██  ██ ██   ██    ██    
██      ██ ██      ██████      ██████       ███████ ██ ██████    ████   ██ ██   ██    ██    
                                                                                            
                                                                                            ${ENDCOLOR}\n"
}
logo_install_mdp_libvirt

echo -e "${ORANGE}Groups!${ENDCOLOR}"
VIRTGROUP="libvirt"
if grep -q $VIRTGROUP /etc/group; then
  echo -e "${GREEN}libvirt group exist!${ENDCOLOR}"
else
  sudo groupadd libvirt
  sudo usermod -a -G libvirt "$(whoami)"
  echo -e "${ORANGE}Done!${ENDCOLOR}"
fi
sleep 3

echo -e "${ORANGE}Mpd!${ENDCOLOR}"
	if systemctl is-enabled --quiet mpd.service; then
        echo -e "${RED}Disabling${ENDCOLOR} ${GREEN} and stopping the global mpd service!${ENDCOLOR}"
        if sudo systemctl disable --now mpd.service >/dev/null 2> >(tee -a "$ERROR_LOG"); then
            sleep 1
            echo -e "${GREEN}Global MPD service ${RED}disabled${ENDCOLOR} ${GREEN}successfully!${ENDCOLOR}"
        else
            sleep 1
            echo -e "${RED}Global MPD service disabled successfully!${ENDCOLOR}"
            log_error "Failed to disable global MPD service"
		fi
	fi

    echo -e "${ORANGE}Enabling and starting the user-level mpd service!${ENDCOLOR}"

    if systemctl --user enable --now mpd.service >/dev/null 2> >(tee -a "$ERROR_LOG"); then
        sleep 1
        echo -e "${GREEN}User-level MPD service enabled successfully!${ENDCOLOR}"
    else
        sleep 1
        echo -e "${RED}Please check %sRiceError.log!${ENDCOLOR}"
        log_error "Failed to enable user-level MPD service"
    fi
sleep 3
clear

########## --------- Замена шелла на zsh ---------- ##########
logo_install_zsh () {
	echo -en "${GREEN}                                  
███████ ███████ ██   ██ 
   ███  ██      ██   ██ 
  ███   ███████ ███████ 
 ███         ██ ██   ██ 
███████ ███████ ██   ██ 
                        
                        ${ENDCOLOR}\n"
}
logo_install_zsh

	if [[ $SHELL != "/usr/bin/zsh" ]]; then
        echo -e "${YELLOW}Changing your shell to zsh...${ENDCOLOR}"

        if chsh -s /usr/bin/zsh 2> >(tee -a "$ERROR_LOG"); then
            echo -e "${GREEN}Shell changed to zsh successfully!${ENDCOLOR}"
        else
            echo -e "${RED}Error changing your shell to zsh. Please check %sRiceError.log${ENDCOLOR}"
            log_error "Failed to change shell to zsh"
        fi
    else
        echo -e "${GREEN}Your shell is already zsh!${ENDCOLOR}"
    fi
sleep 3
clear

########## --------- Выход ---------- ##########
logo_install_reboot () {
	echo -en "${GREEN}                                  
██████  ███████ ██████   ██████   ██████  ████████ 
██   ██ ██      ██   ██ ██    ██ ██    ██    ██    
██████  █████   ██████  ██    ██ ██    ██    ██    
██   ██ ██      ██   ██ ██    ██ ██    ██    ██    
██   ██ ███████ ██████   ██████   ██████     ██    
                                                   
                                                   ${ENDCOLOR}\n"
}
logo_install_reboot

echo -e "${YELLOW}The installation is complete, you ${GREEN}need${ENDCOLOR}${YELLOW} to restart your machine.${ENDCOLOR}"

	while true; do
		read -rp " Reboot now? [y/N]: " yn
		case $yn in
			[Yy]* )
        echo -e "${YELLOW}Rebooting now...${ENDCOLOR}"
				sleep 3
				reboot
				break
				;;
			[Nn]* )
        echo -e "${GREEN}OK, remember to restart later!${ENDCOLOR}"
				break
				;;
			* )
        echo -e "${YELLOW}Please answer yes or no!${ENDCOLOR}"
				;;
		esac
	done