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
backup_folder=~/.Backup_files
date=$(date +%Y%m%d-%H%M%S)
yay_git="https://aur.archlinux.org/yay.git"
repo_url="https://github.com/igorjoxa1118/Tokio_night"


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

dependencias=(base-devel yad cmus rsync mpv jq git socat mpd polkit-gnome stalonetray kitty lsd ranger \
              micro blueman mousepad ristretto firefox thunar thunar-volman thunar-media-tags-plugin thunar-archive-plugin \
              polybar rofi dunst xdg-user-dirs nitrogen picom yt-dlp \
              fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-autosuggestions \
              zsh-history-substring-search starship bluez-utils bluez-tools bluez-plugins bluez-libs bluez blueman)

dependencias_yay=(zscroll-git ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling musikcube pamac-aur kazam)

if [ ! -f /usr/bin/firefox ];then 
 sudo pacman -S firefox
 exit;
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
	if [ ! -e "$HOME/.config/user-dirs.dirs" ]; then
		xdg-user-dirs-update
		echo -e "${LIGHTBLUE}Creating xdg-user-dirs"
	fi
sleep 2 
clear

                                          ########## ---------- Установка yay---------- ##########
logo "Do you have yay? Install it?"

clone_yay() {
    if [[ -d "$HOME/Downloads" ]]; then
       cd "$HOME/Downloads" || exit
       git clone $yay_git
       cd "$HOME/Downloads/yay" || exit
       makepkg -si --noconfirm
    else
       cd "$HOME" || exit
       git clone $yay_git
       cd "$HOME/yay" || exit
       makepkg -si --noconfirm
    fi
}

while true; do
	read -rp "Do you want yay? [y/N]: " yn
		case $yn in
			[Yy]* ) clone_yay && break;;
			[Nn]* ) break;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

                                          ########## ---------- Установка пакетов AUR---------- ##########

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

                                          ########## ---------- Резервная копия файлов и каталогов ---------- ##########

logo "Backup files"
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



func_install_dots() {
logo "Install dotfiles"
cd "$pwd"/user || exit
rsync -aAEHSXxr "$pwd"/user/.[^.]* "$HOME"
cp -rf .* "$HOME"
sed -i "s/vir0id/${user}/g" "$HOME/.config/nitrogen/bg-saved.cfg"
sed -i "s/vir0id/${user}/g" "$HOME/.config/nitrogen/nitrogen.cfg"
sed -i "s/vir0id/${user}/g" "$HOME/.zshrc"
echo -e "${GRE}Copy dots succesfully!"
sleep 2
clear

########## ---------- Установка сведений о батареи ---------- ##########
logo "Power supply install"

ad=$(ls /sys/class/power_supply/ | awk "NR==1 { print $2 }" | grep A)
bat=$(ls /sys/class/power_supply/ | awk "NR==2 { print $2 }" | grep B)

sed -i "s/AC/${ad}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
sed -i "s/BAT0/${bat}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
echo -e "${PURPLE}Power supply install done!"
sleep 2
clear

### -- Переменные для сетевых интерфейсов -- ###
logo "Connection interfaces install"

en_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
et_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wl_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

### --- Проверка проводных сетевых интерфейсов. Добавляем интерфейсы в конфиги. --- ###
if [ ! -z "$en_int" ]; then
sed -i "s/enp59s0/${en_int}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
else
  if [ ! -z "$et_int" ]; then
  sed -i "s/enp59s0/${et_int}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
  else
  read -p "What is you Wired connection interface?(Example: eth0, enp59s0): " et_int_custom
  sed -i "s/enp59s0/${et_int_custom}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
  fi
fi

### --- Проверка безпроводных сетевых интерфейсов. Добавляем интерфейсы в конфиги. --- ###
if [ ! -z "$wl_int" ]; then
sed -i "s/wlp0s20f3/${wl_int}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
else
read -p "What is you Wireless connection interface?(Example: wlan0, wlp0s20f3): " wl_int_custom
sed -i "s/wlp0s20f3/${wl_int_custom}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
fi
}
echo -e "${LIGHTCYAN}Connection interfaces install done!"
sleep 2
clear

### --- Завершение копирования dot-файлов --- ###
func_install_dots
sleep 2
clear

### --- Установка темы и конфигов Firefox --- ###
logo "Firefox theme install"
grep_ff=$(ls ~/.mozilla/firefox | grep default-release)

copy_ff_func() {
if [ ! -z "$grep_ff" ]; then
for ff_themes in $repo_dir/firefox/*; do
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



nvidia_detect()
{
  logo "Check nvidia driver"
  blacklight=$(ls -1 /sys/class/backlight/)

    if [ $(lspci -k | grep -A 2 -E "(VGA|3D)" | grep -i nvidia | wc -l) -gt 0 ]; then
        echo -e "${ORANGE}Nvidia card found!"
    else
        rm -rf "$HOME/.config/i3/polybar/Tokio_night/config.ini"
        cd "$pwd"/not_nvidia_polybar || exit
        cp -R config.ini "$HOME/.config/i3/polybar/Tokio_night/"
        sed -i "s/nvidia_wmi_ec_backlight/${blacklight}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
        echo -e "${CYAN}Nvidia card no found!"
    fi
}
nvidia_detect
sleep 2
clear

                                        ### ---------- Включение сервиса MPD ---------- ###

logo "Enabling mpd service"

### --- Проверка, включена ли служба mpd на глобальном (системном) уровне. --- ###

	if systemctl is-enabled --quiet mpd.service; then
		echo -e "${LIGHTBLUE}Disabling and stopping the global mpd service"
		sudo systemctl stop mpd.service
		sudo systemctl disable mpd.service
	fi

echo -e "${ORANGE}Enabling and starting the user-level mpd service"
sudo systemctl enable --now mpd.service

echo -e "${LIGHTGREEN}Done!!"
sleep 2
clear

########## --------- Замена шелла на zsh ---------- ##########



shell_change() {
  logo "Changing default shell to zsh"
	if [[ $SHELL != "/usr/bin/zsh" ]]; then
		echo -e "${ORANGE}Changing your shell to zsh. Your root password is needed."
		# Переключиться на zsh
		chsh -s /usr/bin/zsh
		echo -e "${LIGHTBLUE}Shell changed to zsh. Please reboot."
	else
		echo -e "${CYAN}Your shell is already zsh! Installation finished, now reboot"
	fi
}


if shell_change; then
reboot
fi