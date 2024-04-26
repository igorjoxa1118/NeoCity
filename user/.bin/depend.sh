#!/usr/bin/bash

dependencias=(base-devel dunst imagemagick \
libwebp maim mpc neovim ncmpcpp npm pamixer \
papirus-icon-theme \
redshift rustup ttf-inconsolata ttf-jetbrains-mono ttf-jetbrains-mono-nerd \
ttf-joypixels eww ttf-terminus-nerd ueberzug webp-pixbuf-loader xclip \
xdo catppuccin-cursors-mocha ttf-nerd-fonts-symbols ttf-nerd-fonts-symbols-common \
ttf-nerd-fonts-symbols-mono yad cmus jgmenu rsync mpv jq git socat mpd polkit-gnome \
stalonetray kitty lsd ranger micro blueman mousepad ristretto firefox thunar thunar-volman \
thunar-media-tags-plugin thunar-archive-plugin polybar rofi xdg-user-dirs engrampa bc \
nitrogen picom yt-dlp fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-autosuggestions \
zsh-history-substring-search starship bluez-utils bluez-tools bluez-plugins bluez-libs bluez \
zziplib zip xarchiver unzip unarj unarchiver p7zip libzip karchive gnome-autoar file-roller \
cpio arj perl libarchive telegram-desktop code discord gimp blender krita kdenlive kodi \
kodi-addon-inputstream-adaptive kodi-dev kodi-eventclients kodi-platform p8-platform vde2)

dependencias_yay=(cava zscroll-git ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
zenity-gtk3 musikcube i3lock-color pamac-aur kazam kodi-addon-pvr-iptvsimple hypnotix)

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

########## ---------- Установка пакетов AUR---------- ##########

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
sleep 2
echo "Done"