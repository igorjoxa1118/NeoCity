#!/bin/bash
#set -x

CRE=$(tput setaf 1)
CYE=$(tput setaf 3)
CGR=$(tput setaf 2)
CBL=$(tput setaf 4)
BLD=$(tput bold)
CNC=$(tput sgr0)

RED='\033[0;31m'
GRE='\033[0;32m'
CYA='\033[0;36m'

backup_folder=~/.Backup_files
date=$(date +%Y%m%d-%H%M%S)
yay_git="https://aur.archlinux.org/yay.git"
repo_url="https://github.com/igorjoxa1118/Tokio_night"
repo_dir="$HOME/Tokio_night"

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
    echo "This script MUST NOT be run as root user."
    exit 1
fi

                                          ########## ---------- Приветики пистолетики =) ---------- ##########

logo "Welcome!"
printf '%s%s Please launch and close Firefox if you have it. Otherwise, the Firefox theme wont install the first time.\nThis script checks to see if you have the necessary requirements, and if not, it will install them.%s\n\n' "${BLD}" "${CRE}" "${CNC}"

while true; do
	read -rp " Do you wish to continue? [y/N]: " yn
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
		echo "Creating xdg-user-dirs"
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
	read -rp " Do you want yay? [y/N]: " yn
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

                                          ########## ---------- Клонирование Tokio night dots! ---------- ##########

logo "Downloading dotfiles"

#### Клонировать если репозиторий dot-файлами не существует
if [ ! -d "$repo_dir" ]; then
   printf "Cloning dotfiles in %s\n" "$repo_url"
   git clone --depth=1 "$repo_url" "$repo_dir"
   else
   echo "Dotfile folder exist"
fi
sleep 2
clear
                                          ########## ---------- Резервная копия файлов и каталогов ---------- ##########

logo "Backup files"
printf "Backup files will be stored in %s%s%s/.Backup_files%s \n\n" "${BLD}" "${CRE}" "$HOME" "${CNC}"

rsync -aAEHSXxr --exclude=".cache/mozilla/*" ~/.[^.]* $backup_folder

printf "%s%sDone!!%s\n\n" "${BLD}" "${CGR}" "${CNC}"
sleep 2


for del in polybar rofi picom.conf; do
   rm -rf ~/.config/$del
   echo "$del deleted"
done

sleep 2
clear
                                          ########## ---------- Установка dot-файлов и темы для Firefox ---------- ##########

logo "Install dotfiles"

func_install_dots() {

### -- Переменные для сетевых интерфейсов -- ###

en_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
et_int=$(ip -o link show | sed -rn '/^[0-9]+: en/{s/.: ([^:]*):.*/\1/p}')
wl_int=$(ip -o link show | sed -rn '/^[0-9]+: wl/{s/.: ([^:]*):.*/\1/p}')

cd "$repo_dir"/user || exit

cp -rf .* "$HOME"

sed -i "s/vir0id/${user}/g" "$HOME/.config/nitrogen/bg-saved.cfg"
sed -i "s/vir0id/${user}/g" "$HOME/.config/nitrogen/nitrogen.cfg"
sed -i "s/vir0id/${user}/g" "$HOME/.zshrc"

### --- Проверка проводных сетевых интерфейсов. Добавляем интерфейсы в конфиги. --- ###

if [ ! -z "$en_int" ]; then
sed -i "s/enp59s0/${en_int}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
else
  if [ ! -z "$et_int" ]; then
  sed -i "s/enp59s0/${et_int}/g" "$HOME"/.config/i3/polybar/Tokio_night/modules
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

### --- Завершение копирования dot-файлов --- ###

if func_install_dots; then
  printf "%s%s%s ${GRE}Copy dots succesfully!%s\n" 
else
  printf "%s%s%s ${RED}Copy dots fieled, you must do it manually%s\n"
fi

### --- Установка темы и конфигов Firefox --- ###

grep_ff=$(ls ~/.mozilla/firefox | grep default-release)

copy_ff_func() {
if [ ! -z "$grep_ff" ]; then
for ff_themes in $repo_dir/firefox/*; do
  cp -R "${ff_themes}" ~/.mozilla/firefox/"$grep_ff"
  if [ $? -eq 0 ]; then
	printf "%s%s%s folder copied succesfully!%s\n" "${BLD}" "${CGR}" "${ff_themes}" "${CNC}"
	sleep 1
  else
	printf "%s%s%s failed to been copied, you must copy it manually%s\n" "${BLD}" "${CRE}" "${ff_themes}" "${CNC}"
	sleep 1
  fi
done
fi
}

if [ ! -z "$grep_ff" ]; then
   copy_ff_func
else
   printf "%s%s%s Please start FF befor run this script%s\n" "${BLD}" "${CRE}" "$grep_ff" "${CNC}"
   exit 1
fi

sleep 2
clear
                                        #### ------- Проверка видеокарты. Если карта отсутствует, то модули на polybar будут другие --- ###

logo "Check nvidia driver"

nvidia_detect()
{
    if [ $(lspci -k | grep -A 2 -E "(VGA|3D)" | grep -i nvidia | wc -l) -gt 0 ]; then
        echo "Nvidia card is found. All is ok"
    else
        rm -rf "$HOME/.config/i3/polybar/Tokio_night/config.ini"
        cd "$repo_dir"/not_nvidia || exit
        cp -R config.ini "$HOME/.config/i3/polybar/Tokio_night/"
    fi
}
nvidia_detect
sleep 2
clear

                                        ### ---------- Включение сервиса MPD ---------- ###

logo "Enabling mpd service"

### --- Проверка, включена ли служба mpd на глобальном (системном) уровне. --- ###

	if systemctl is-enabled --quiet mpd.service; then
		printf "\n%s%sDisabling and stopping the global mpd service%s\n" "${BLD}" "${CBL}" "${CNC}"
		sudo systemctl stop mpd.service
		sudo systemctl disable mpd.service
	fi

printf "\n%s%sEnabling and starting the user-level mpd service%s\n" "${BLD}" "${CYE}" "${CNC}"
sudo systemctl enable --now mpd.service

printf "%s%sDone!!%s\n\n" "${BLD}" "${CGR}" "${CNC}"
sleep 2
clear

########## --------- Замена шелла на zsh ---------- ##########

logo "Changing default shell to zsh"

shell_change() {
	if [[ $SHELL != "/usr/bin/zsh" ]]; then
		printf "\n%s%sChanging your shell to zsh. Your root password is needed.%s\n\n" "${BLD}" "${CYE}" "${CNC}"
		# Переключиться на zsh
		chsh -s /usr/bin/zsh
		printf "%s%sShell changed to zsh. Please reboot.%s\n\n" "${BLD}" "${CGR}" "${CNC}"
	else
		printf "%s%sYour shell is already zsh\nGood bye! installation finished, now reboot%s\n" "${BLD}" "${CGR}" "${CNC}"
	fi
}


if shell_change; then
reboot
fi