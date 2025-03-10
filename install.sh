#!/bin/bash
#set -x

##----------------
#--Colors
##----------------
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
INSTALL_LOG="$HOME/RiceInstall.log"
current_dir=$(pwd)
home_dir=$HOME

##-----------------
#--Functions
##-----------------

# Logging function
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$INSTALL_LOG"
}

# Error logging function
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" >> "$ERROR_LOG"
    echo -e "${RED}ERROR: $1${ENDCOLOR}"
}

# Check if a package is installed
is_installed() {
    pacman -Qq "$1" &> /dev/null
}

# Install packages with pacman
install_packages() {
    local packages=("$@")
    for pkg in "${packages[@]}"; do
        if ! is_installed "$pkg"; then
            echo -e "${YELLOW}Installing $pkg...${ENDCOLOR}"
            if sudo pacman -S --noconfirm "$pkg" >> "$INSTALL_LOG" 2>> "$ERROR_LOG"; then
                echo -e "${GREEN}$pkg installed successfully.${ENDCOLOR}"
            else
                log_error "Failed to install $pkg"
            fi
        else
            echo -e "${GREEN}$pkg is already installed.${ENDCOLOR}"
        fi
    done
}

# Install AUR packages with paru
install_aur_packages() {
    local packages=("$@")
    for pkg in "${packages[@]}"; do
        if ! is_installed "$pkg"; then
            echo -e "${YELLOW}Installing $pkg from AUR...${ENDCOLOR}"
            if paru -S --noconfirm "$pkg" >> "$INSTALL_LOG" 2>> "$ERROR_LOG"; then
                echo -e "${GREEN}$pkg installed successfully.${ENDCOLOR}"
            else
                log_error "Failed to install $pkg from AUR"
            fi
        else
            echo -e "${GREEN}$pkg is already installed.${ENDCOLOR}"
        fi
    done
}

# Backup user files
backup_files() {
    echo -e "${CYAN}Backing up files to $backup_folder...${ENDCOLOR}"
    mkdir -p "$backup_folder"
    rsync -aAEHSXxr --delete --exclude=".cache/mozilla/*" ~/.[^.]* "$backup_folder"
    echo -e "${GREEN}Backup completed.${ENDCOLOR}"
}

# Install dotfiles
install_dotfiles() {
    echo -e "${CYAN}Installing dotfiles...${ENDCOLOR}"
    cp -rf "$current_dir"/user/.* "$home_dir"
    echo -e "${GREEN}Dotfiles installed.${ENDCOLOR}"
}

# Install SDDM theme
install_sddm_theme() {
    echo -e "${CYAN}Installing SDDM theme...${ENDCOLOR}"
    if [ -d /etc/sddm.conf.d/ ]; then
        sudo cp -rf "$current_dir"/sddm/sddm.conf.d /etc/
        sudo cp -rf "$current_dir"/sddm/catppuccin-mocha /usr/share/sddm/themes
        sudo systemctl enable sddm.service >> "$INSTALL_LOG" 2>> "$ERROR_LOG"
        echo -e "${GREEN}SDDM theme installed.${ENDCOLOR}"
    else
        log_error "SDDM configuration directory not found."
    fi
}

# Install GRUB theme
install_grub_theme() {
    echo -e "${CYAN}Installing GRUB theme...${ENDCOLOR}"
    GRUB_THEME_DIR="/usr/share/grub/themes"
    grub_theme="catppuccin-mocha-grub-theme"
    if [ ! -d "$GRUB_THEME_DIR"/"$grub_theme" ]; then
        sudo cp -rf "$current_dir"/grub_themes/"$grub_theme" "$GRUB_THEME_DIR"
    fi
    if [ -f /etc/default/grub ]; then
        sudo sed -i "s|.*GRUB_THEME=.*|GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"|" /etc/default/grub
        sudo grub-mkconfig -o /boot/grub/grub.cfg >> "$INSTALL_LOG" 2>> "$ERROR_LOG"
        echo -e "${GREEN}GRUB theme installed.${ENDCOLOR}"
    else
        log_error "GRUB configuration file not found."
    fi
}

# Add user to libvirt group
add_user_to_libvirt() {
    echo -e "${CYAN}Adding user to libvirt group...${ENDCOLOR}"
    VIRTGROUP="libvirt"
    if ! grep -q $VIRTGROUP /etc/group; then
        sudo groupadd libvirt
    fi
    sudo usermod -a -G libvirt "$(whoami)"
    sudo systemctl enable --now libvirtd >> "$INSTALL_LOG" 2>> "$ERROR_LOG"
    echo -e "${GREEN}User added to libvirt group.${ENDCOLOR}"
}

# Change shell to zsh
change_shell_to_zsh() {
    echo -e "${CYAN}Changing shell to zsh...${ENDCOLOR}"
    if [[ $SHELL != "/usr/bin/zsh" ]]; then
        if chsh -s /usr/bin/zsh >> "$INSTALL_LOG" 2>> "$ERROR_LOG"; then
            echo -e "${GREEN}Shell changed to zsh.${ENDCOLOR}"
        else
            log_error "Failed to change shell to zsh."
        fi
    else
        echo -e "${GREEN}Shell is already zsh.${ENDCOLOR}"
    fi
}

# Main function
main() {
    # Check if running as root
    if [ "$(id -u)" = 0 ]; then
        echo -e "${RED}This script MUST NOT be run as root user.${ENDCOLOR}"
        exit 1
    fi

    # Check for required tools
    if ! command -v git &> /dev/null; then
        echo -e "${RED}git is not installed. Please install git and run the script again.${ENDCOLOR}"
        exit 1
    fi

    # Start installation
    echo -e "${YELLOW}Starting installation...${ENDCOLOR}"

    # Install required packages
    dependencias=(base base-devel sof-firmware alacritty brightnessctl dunst bottom imagemagick \
                  libwebp maim mpc ncmpcpp npm pamixer neovim xorg-xhost glib2 xsettingsd \
                  papirus-icon-theme pacman-contrib physlock playerctl python-gobject \
                  redshift rust ttf-inconsolata ttf-jetbrains-mono ttf-jetbrains-mono-nerd \
                  ttf-joypixels ttf-terminus-nerd ueberzug webp-pixbuf-loader xclip \
                  xdo ttf-nerd-fonts-symbols ttf-nerd-fonts-symbols-common easyeffects \
                  ttf-nerd-fonts-symbols-mono yad cmus rsync mpv jq git socat mpd polkit-gnome \
                  amd-ucode arch-install-scripts bind-tools broadcom-wl btrfs-progs busybox clonezilla crda curl \
                  darkhttpd ddrescue dhclient dhcpcd diffutils dmraid dosfstools edk2-shell efibootmgr ethtool \
                  exa exfatprogs f2fs-tools fsarchiver gnu-netcat gpm gptfdisk haveged hdparm intel-ucode \
                  irssi jfsutils kitty-terminfo lftp lsscsi lvm2 lynx mc mdadm mkinitcpio mkinitcpio-archiso \
                  mkinitcpio-nfs-utils nano nano-syntax-highlighting nbd ndisc6 nfs-utils nilfs-utils \
                  nmap ntfs-3g nvme-cli openconnect openssh openvpn partclone parted partimage ppp pptpclient reflector \
                  reiserfsprogs rp-pppoe rxvt-unicode-terminfo sdparm sg3_utils smartmontools tree wget \
                  xsel awesome-terminal-fonts zsh-completions zshdb qpwgraph lsp-plugins lsp-plugins-clap lsp-plugins-docs lsp-plugins-gst \
                  lsp-plugins-ladspa lsp-plugins-lv2 lsp-plugins-standalone lsp-plugins-vst lsp-plugins-vst3 \
                  adobe-source-code-pro-fonts adobe-source-sans-pro-fonts adobe-source-serif-pro-fonts \
                  dex dmenu eog gnome-backgrounds gnome-keyring gnome-themes-extra gvfs gvfs-afc gvfs-goa gvfs-google gvfs-gphoto2 \
                  gvfs-mtp gvfs-nfs gvfs-smb kvantum-qt5 lollypop lxsession pcmanfm qt5ct sddm \
                  totem xdg-user-dirs-gtk xfce4-screenshooter alsa-utils archinstall b43-fwcutter \
                  bcachefs-tools bolt brltty cryptsetup dmidecode e2fsprogs espeakup fatresize foot-terminfo \
                  gpart hyperv iw iwd ldns less libfido2 libusb-compat modemmanager mtools open-iscsi open-vm-tools \
                  openpgp-card-tools pcsclite pv qemu-guest-agent qemu virt-manager libvirt virt-viewer dnsmasq bridge-utils \
                  libguestfs refind screen sequoia-sq squashfs-tools systemd-resolvconf tcpdump \
                  terminus-font tmux tpm2-tools tpm2-tss udftools usb_modeswitch usbmuxd usbutils vpnc wireless-regdb \
                  wireless_tools wpa_supplicant wvdial xfsprogs xl2tpd bash-completion libxinerama make xterm xorg-xrdb \
                  stalonetray kitty lsd ranger micro blueman mousepad ristretto firefox firefox-dark-reader firefox-ublock-origin thunar thunar-volman \
                  thunar-media-tags-plugin thunar-archive-plugin polybar rofi xdg-user-dirs engrampa bc \
                  nitrogen feh picom yt-dlp fzf mcfly neofetch zsh zsh-syntax-highlighting zsh-autosuggestions \
                  zsh-history-substring-search starship bluez-utils bluez-tools bluez-plugins bluez-libs bluez \
                  zziplib unarj libzip karchive gnome-autoar file-roller otf-firamono-nerd ttf-meslo-nerd \
                  cpio arj perl libarchive telegram-desktop code discord gimp blender krita kdenlive kodi \
                  kodi-addon-inputstream-adaptive kodi-dev kodi-eventclients kodi-platform p8-platform vde2 xorg-xdpyinfo xorg-xwininfo \
                  xorg-xkill xorg-xprop xorg-xrandr xorg-xsetroot xdotool bzip2 gzip lrzip lz4 lzip lzop xz zstd p7zip zip unzip unrar \
                  yazi unarchiver xarchiver qt6-svg qt6-declarative qt5-quickcontrols2 qt5-graphicaleffects ffmpeg poppler fd ripgrep qbittorrent zoxide)

    install_packages "${dependencias[@]}"

    # Install AUR packages
    dependencias_paru=(cava tor-browser-bin ymuse-git zscroll-git eww-git musnify-mpd gnome-icon-theme zsh-theme-powerlevel10k powerline-fonts-git\
                       catppuccin-cursors-mocha ttf-meslo-nerd-font-powerlevel10k ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
                       i3lock-color gdown kazam kodi-addon-pvr-iptvsimple hypnotix)

    install_aur_packages "${dependencias_paru[@]}"

    # Backup files
    backup_files

    # Install dotfiles
    install_dotfiles

    # Install SDDM theme
    install_sddm_theme

    # Install GRUB theme
    install_grub_theme

    # Add user to libvirt group
    add_user_to_libvirt

    # Change shell to zsh
    change_shell_to_zsh

    # Final message
    echo -e "${YELLOW}Installation complete. You may need to reboot your system.${ENDCOLOR}"
    while true; do
        read -rp "Reboot now? [y/N]: " yn
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
}

# Run main function
main