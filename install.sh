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

##-----------------
#---Vars
##-----------------

backup_folder=~/.Backup_files
date=$(date +%Y%m%d-%H%M%S)
repo_url="https://github.com/igorjoxa1118/NeoCity"
paru_url="https://aur.archlinux.org/paru-bin.git"
home_dir=$HOME
current_dir=$(pwd)
GRUB_THEME_DIR="/usr/share/grub/themes"
grub_theme="catppuccin-mocha-grub-theme"

##-----------------
#--Logo
##-----------------

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

########## ---------- Скрипт должен быть запущен от sudo ---------- ##########

if [ "$(id -u)" = 0 ]; then
    echo -e "${LIGHTBLUE}This script MUST NOT be run as root user."
    exit 1
fi

########## ---------- Приветики пистолетики =) ---------- ##########

logo "Welcome!"
printf '%s%s Please launch and close Firefox if you have it. Otherwise, the Firefox theme wont install the first time.\nThis script checks to see if you have the necessary requirements, and if not, it will install them.%s\n\n' "${BLD}" "${CRE}" "${CNC}"

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

dependencias=(base-devel alacritty brightnessctl dunst imagemagick \
              libwebp maim mpc neovim ncmpcpp npm pamixer neovim\
              papirus-icon-theme pacman-contrib physlock playerctl python-gobject \
              redshift rustup ttf-inconsolata ttf-jetbrains-mono ttf-jetbrains-mono-nerd \
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
              xorg-xkill xorg-xprop xorg-xrandr xorg-xsetroot xdotool bzip2 gzip lrzip lz4 lzip lzop xz zstd p7zip zip unzip unrar unarchiver xarchiver)



dependencias_paru=(cava zscroll-git eww-git gnome-icon-theme catppuccin-cursors-mocha ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
              zenity-gtk3 i3lock-color gdown pamac-aur kazam kodi-addon-pvr-iptvsimple hypnotix)

pipewire_pkg=(gst-plugin-pipewire libpipewire libwireplumber pipewire pipewire-alsa \
              pipewire-audio pipewire-jack pipewire-pulse pipewire-v4l2 pipewire-x11-bell \
              pipewire-zeroconf qemu-audio-pipewire wireplumber lib32-libpipewire \
              multilib/lib32-pipewire lib32-pipewire-jack)

pipewire_pkg_yay=(pipewire-support)

if [ ! -f /usr/bin/firefox ]; then 
 sudo pacman -S firefox --noconfirm
 printf "%s%sStart Firefox manualy!...%s\n" "${BLD}" "${CBL}" "${CNC}" 
 exit;
fi

if [ -f /usr/bin/zenity ]; then
  sudo pacman -Rdd zenity --noconfirm
elif [ -f /usr/bin/i3lock ]; then
  sudo pacman -Rdd i3lock --noconfirm
fi

if [ -f /usr/bin/lxappearance ]; then
  sudo pacman -R lxappearance --noconfirm
  sudo pacman -S lxappearance-gtk3 --noconfirm
fi

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

########## ---------- Проверка существование домашних каталогов ---------- ##########

# Проверка того, что архив user-dirs.dirs не существует в ~/.config
	if [ ! -e "$home_dir/.config/user-dirs.dirs" ]; then
		xdg-user-dirs-update
		echo -e "${LIGHTBLUE}Creating xdg-user-dirs"
	fi
sleep 2 
clear

########## ---------- Установка paru---------- ##########
logo "Do you have paru? Install it?"

clone_paru() {
# Installing Paru
if command -v paru >/dev/null 2>&1; then
    printf "%s%sParu is already installed%s\n" "${BLD}" "${CGR}" "${CNC}"
else
    printf "%s%sInstalling paru%s\n" "${BLD}" "${CBL}" "${CNC}"
    {
        cd "$home_dir" || exit
        git clone $paru_url
        cd paru-bin || exit
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

function pipewire_func() {
 if [ -f /usr/bin/pulseaudio ]; then
  sudo pacman -Rdd pulseaudio pulseaudio-bluetooth pulseaudio-alsa pulseaudio-equalizer pulseaudio-jack pulseaudio-lirc pulseaudio-zeroconf --noconfirm
 elif [ ! -f /usr/bin/pipewire ]; then
  sudo pacman -S "${pipewire_pkg[@]}" --noconfirm
  paru -S "${pipewire_pkg_yay[@]}" --noconfirm
 else 
  echo -e "${ORANGE}Somthing wrong!!"
 fi
}

while true; do
	read -rp "Do you want Pipewire? [y/N]: " yn
		case $yn in
			[Yy]* ) pipewire_func && break;;
			[Nn]* ) break;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

########## ---------- Резервная копия файлов и каталогов ---------- ##########
logo "Backup files"
sleep 2
echo -e "${CYAN}Backup files will be stored in .Backup_files"

rsync -aAEHSXxr --exclude=".cache/mozilla/*" ~/.[^.]* $backup_folder

echo -e "${ORANGE}Done!!"
sleep 2


for del in polybar rofi picom.conf; do
   rm -rf ~/.config/$del
   echo -e "${YELLOW}$del deleted"
done
clear

########## ---------- Установка dot-файлов и темы для Firefox ---------- ##########
logo "Install dotfiles"
sleep 2
func_install_dots() {
cp -rf "$current_dir"/user/.* "$home_dir"
cp -rf "$current_dir"/user/Test_Musik "$home_dir"
sud cp -rf "$current_dir"/grub_themes/catppuccin-mocha-grub-theme /usr/share/grub/themes/
clear
echo -e "${GRE}Copy dots succesfully!"
sleep 2
  if [ -d $current_dir/pkgs_virOS ]; then
    sudo pacman -U $current_dir/pkgs_virOS/*.zst --noconfirm
  else
    cd $current_dir
    if [ ! -d $current_dir/pkgs_virOS ]; then
    gdown --folder 19SlCmblUJts_I5dlAwd2C3tq7q2-wLbS
    echo -e "${GRE}Packages in system!"
    sleep 2
    sudo pacman -U $current_dir/pkgs_virOS/*.zst --noconfirm
  fi

sudo sed -i "s/Inherits=.*/Inherits=catppuccin-mocha-teal-cursors/g" /usr/share/icons/default/index.theme

##-------------------
#--Grub themes apply
##-------------------

    if grep "GRUB_THEME=" /etc/default/grub 2>&1 >/dev/null; then
      #Replace GRUB_THEME
      sudo sed -i "s|.*GRUB_THEME=.*|GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"|" /etc/default/grub
    else
      #Append GRUB_THEME
      sudo echo "GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"" >> /etc/default/grub
    fi

##-------------------
#--Install bin files
##-------------------

if [[ ! -f "/usr/local/bin/toggle-conkeww" ]]; then
  sudo mkdir -p /usr/share/garuda/jgmenu/
  sudo cp -r "$home_dir"/.config/i3/bin/toggle-conkeww /usr/local/bin
  sudo cp -r "$home_dir"/.config/i3/bin/i3-new-workspace /usr/local/bin
  sudo chmod 755 /usr/local/bin/i3-new-workspace
  sudo cp -r "$home_dir"/.config/i3/bin/colors /usr/local/bin
  sudo cp -r "$home_dir"/.config/i3/bin/def-dmenu /usr/local/bin
  sudo cp -r "$home_dir"/.config/i3/bin/def-nmdmenu /usr/local/bin
  sudo cp -r "$home_dir"/.config/jgmenu/MenuIcons /usr/share/garuda/jgmenu/ 
else
sudo cp -r "$home_dir"/.config/jgmenu/MenuIcons /usr/share/garuda/jgmenu/
fi
}

### --- Завершение копирования dot-файлов --- ###
func_install_dots
sleep 2
clear

########## ---------- Установка сведений о батареи ---------- ##########
logo "Power supply install"
sleep 2
ad=$(ls /sys/class/power_supply/ | awk "NR==1 { print $2 }" | grep A)
bat=$(ls /sys/class/power_supply/ | awk "NR==2 { print $2 }" | grep B)

sed -i "s/AC/${ad}/g" "$home_dir"/.config/i3/rices/emilia/modules.ini
sed -i "s/BAT0/${bat}/g" "$home_dir"/.config/i3/rices/emilia/modules.ini
echo -e "${PURPLE}Power supply install done!"
sleep 2
clear

### -- Переменные для сетевых интерфейсов -- ###
logo "Connection interfaces install"
sleep 2
en_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
et_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wl_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

### --- Проверка проводных сетевых интерфейсов. Добавляем интерфейсы в конфиги. --- ###
if [ ! -z "$en_int" ]; then
sed -i "s/enp1s0/${en_int}/g" "$home_dir"/.config/i3/scripts/system.ini
else
  if [ ! -z "$et_int" ]; then
  sed -i "s/enp1s0/${et_int}/g" "$home_dir"/.config/i3/scripts/system.ini
  else
  read -p "What is you Wired connection interface?(Example: eth0, enp59s0): " et_int_custom
  sed -i "s/enp1s0/${et_int_custom}/g" "$home_dir"/.config/i3/scripts/system.ini
  fi
fi

### --- Проверка безпроводных сетевых интерфейсов. Добавляем интерфейсы в конфиги. --- ###
if [ ! -z "$wl_int" ]; then
sed -i "s/wlp0s20f3/${wl_int}/g" "$home_dir"/.config/i3/scripts/system.ini
else
read -p "What is you Wireless connection interface?(Example: wlp0s20f3, wlp0s20f3): " wl_int_custom
sed -i "s/wlp0s20f3/${wl_int_custom}/g" "$home_dir"/.config/i3/scripts/system.ini
fi

echo -e "${LIGHTCYAN}Connection interfaces install done!"
sleep 2
clear

### --- Установка SDDM --- ###
logo "Install SDDM"
sleep 2

if [ -f /usr/bin/lightdm ]; then
   sudo systemctl disable lightdm.service
   sudo pacman -Rdd lightdm lightdm-gtk-greeter --noconfirm
fi

if [ -d /etc/sddm.conf.d/ ]; then
   sudo cp -rf $current_dir/sddm/sddm.conf.d /etc/
   sudo cp -rf $current_dir/sddm/catppuccin-mocha /usr/share/sddm/themes
   sudo systemctl enable sddm.service
   echo -e "${LIGHTCYAN}Done!"
 else 
   sudo pacman -S sddm --noconfirm
   sudo cp -rf $current_dir/sddm/sddm.conf.d /etc/
   sudo cp -rf $current_dir/sddm/catppuccin-mocha /usr/share/sddm/themes
   sudo systemctl enable sddm.service
   echo -e "${LIGHTCYAN}Done!"
 fi
fi

if [ -d /etc/lightdm ]; then
  sudo rm -rf /etc/lightdm
fi

sleep 2
clear

##-- Установка пользователя в конфиги
logo "Add user configs"
sleep 2
tmpuser=$(whoami)
sed -i "s/vir0id/${tmpuser}/g" "$home_dir"/.config/blender/4.1/config/bookmarks.txt
sed -i "s/vir0id/${tmpuser}/g" "$home_dir"/.gtkrc-2.0
sed -i "s/vir0id/${tmpuser}/g" "$home_dir/.config/nitrogen/bg-saved.cfg"
sed -i "s/vir0id/${tmpuser}/g" "$home_dir/.config/nitrogen/nitrogen.cfg"
sed -i "s/vir0id/${tmpuser}/g" "$home_dir/.zshrc"
sed -i "s/vir0id/${tmpuser}/g" "$home_dir"/.config/gtk-3.0/bookmarks
sed -i "s/vir0id/${tmpuser}/g" "$home_dir"/.local/share/applications/nvim.desktop
sed -i "s/vir0id/${tmpuser}/g" "$home_dir"/.local/share/applications/ranger.desktop
sed -i "s/vir0id/${tmpuser}/g" "$home_dir"/.local/share/applications/zfetch.desktop
sleep 2
clear

### --- Установка темы и конфигов Firefox --- ###
logo "Firefox theme install"
sleep 2
grep_ff=$(ls ~/.mozilla/firefox | grep default-release)

copy_ff_func() {
if [ ! -z "$grep_ff" ]; then
for ff_themes in "$current_dir"/firefox/*; do
  cp -R "${ff_themes}" ~/.mozilla/firefox/"$grep_ff"
  if [ $? -eq 0 ]; then
	echo -e "${LIGHTBLUE}$ff_themes install done!"
	sleep 1
  else
	echo -e "${BLUE}Failed to been copied, you must copy it manually"
	sleep 1
  fi
done
fi
}

if [ ! -z "$grep_ff" ]; then
   copy_ff_func
else
   echo -e "${ORANGE}Please start FF befor run this script"
   exit 1
fi

sleep 2
clear

#### ------- Проверка видеокарты. Если карта отсутствует, то модули на polybar будут другие --- ###
logo "Check nvidia driver"
sleep 2
nvidia_detect() {
  blacklight=$(ls -1 /sys/class/backlight/)

    if [ $(lspci -k | grep -A 2 -E "(VGA|3D)" | grep -i nvidia | wc -l) -gt 0 ]; then
        rm -rf "$home_dir/.config/i3/rices/tealize/config.ini"
        cd "$current_dir"/polybar_rices/nvidia || exit
        cp -R config.ini "$home_dir/.config/i3/rices/tealize/"
        sed -i "s/intel_backlight/${blacklight}/g" "$home_dir"/.config/i3/scripts/system.ini
        echo -e "${ORANGE}Nvidia found!"
    else
        rm -rf "$home_dir/.config/i3/rices/tealize/config.ini"
        cd "$current_dir"/polybar_rices/not_nvidia || exit
        cp -R config.ini "$home_dir/.config/i3/rices/tealize/"
        sed -i "s/intel_backlight/${blacklight}/g" "$home_dir"/.config/i3/scripts/system.ini
        echo -e "${CYAN}Nvidia card no found!"
    fi
}

nvidia_detect
sleep 2
clear

                                        ### ---------- Включение сервиса MPD ---------- ###

### --- Проверка, включена ли служб на глобальном (системном) уровне. --- ###
logo "Enabling MPD services"
sleep 2

if systemctl is-enabled --quiet mpd.service; then
    printf "\n%s%sDisabling and stopping the global mpd service%s\n" "${BLD}" "${CBL}" "${CNC}"
    sudo systemctl stop mpd.service
    sudo systemctl disable mpd.service
  else
      printf "\n%s%sEnabling and starting the user-level mpd service%s\n" "${BLD}" "${CYE}" "${CNC}"
      systemctl --user enable --now mpd.service
      printf "%s%sDone!!%s\n\n" "${BLD}" "${CGR}" "${CNC}"
    sleep 2
    clear
fi

### --- Добавление пользователя в группы вирутальных машин. --- ###
logo "Add libvirt Group"
sleep 2
echo -e "${ORANGE}Enabling Groups"
sleep 2
    sudo usermod -a -G libvirt $(whoami)
    newgrp libvirt
echo -e "${ORANGE}Done!"
sleep 2
clear

########## --------- Замена шелла на zsh ---------- ##########
logo "Changing default shell to zsh"
sleep 2
	if [[ $SHELL != "/usr/bin/zsh" ]]; then
    printf "\n%s%sChanging your shell to zsh. Your root password is needed.%s\n\n" "${BLD}" "${CYE}" "${CNC}"
    # Cambia la shell a zsh
    chsh -s $(which zsh)
    printf "%s%sShell changed to zsh. Please reboot.%s\n\n" "${BLD}" "${CGR}" "${CNC}"
  else
    printf "%s%sYour shell is already zsh\nGood bye! installation finished, now reboot%s\n" "${BLD}" "${CGR}" "${CNC}"
  fi
sleep 2
zsh