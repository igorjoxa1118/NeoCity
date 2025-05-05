#!/bin/bash
#set -x

##----------------
#-- Colors
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
#--- Variables
##-----------------
backup_folder=~/.Backup_files
ERROR_LOG="$HOME/RiceError.log"
home_dir=$HOME
current_dir=$(pwd)
usr=$(whoami)

##-----------------
#-- Functions
##-----------------

# Display colored logo
display_logo() {
    local color="$1"
    local text="$2"
    echo -en "${color}${text}${ENDCOLOR}\n"
}

# Log errors to error log file
log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$ERROR_LOG"
}

# Check if package is installed
is_installed() {
    pacman -Qq "$1" &> /dev/null
}

# Initialize Firefox settings
initialize_firefox() {
    # Check if Firefox is installed
    if ! command -v firefox &> /dev/null; then
        echo -e "${YELLOW}Firefox is not installed. Installing Firefox...${ENDCOLOR}"
        
        if sudo pacman -S firefox --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG"); then
            echo -e "${GREEN}Firefox installed successfully.${ENDCOLOR}"
        else
            echo -e "${RED}Error installing Firefox. Check ${YELLOW}RiceError.log${ENDCOLOR}"
            log_error "Error installing Firefox"
            exit 1
        fi
    fi

    # Firefox profile directory
    PROFILE_DIR="$HOME/.mozilla/firefox/"

    # Launch Firefox to create profile
    echo -e "${YELLOW}Launching Firefox to create profile...${ENDCOLOR}"
    firefox > /dev/null 2>&1 &
    FF_PID=$!

    # Wait for profile creation
    echo -e "${YELLOW}Waiting for Firefox profile creation...${ENDCOLOR}"
    while [ ! -f "$PROFILE_DIR"/*.default-release/prefs.js ]; do
        sleep 1
    done

    # Close Firefox
    kill $FF_PID
    echo -e "${GREEN}Firefox profile created successfully.${ENDCOLOR}"
}

# Install packages from official repositories
install_official_packages() {
    local packages=("$@")
    echo -e "${YELLOW}Checking required packages...${ENDCOLOR}"
    
    for pkg in "${packages[@]}"; do
        if ! is_installed "$pkg"; then
            if sudo pacman -S "$pkg" --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG"); then
                echo -e "${YELLOW}$pkg${ENDCOLOR}${LIGHTBLUE} installed successfully.${ENDCOLOR}"
            else
                echo -e "${YELLOW}$pkg${ENDCOLOR}${RED} failed to install. Check ${YELLOW}RiceError.log${ENDCOLOR}"
                log_error "Failed to install package: $pkg"
            fi
            sleep 1
        else
            echo -e "${YELLOW}$pkg${GREEN} is already installed.${ENDCOLOR}"
            sleep 1
        fi
    done
}

# Install AUR packages using paru
install_aur_packages() {
    local packages=("$@")
    echo -e "${YELLOW}Checking required AUR packages...${ENDCOLOR}"
    
    for pkg in "${packages[@]}"; do
        if ! is_installed "$pkg"; then
            if paru -S --skipreview --noconfirm "$pkg" 2> >(tee -a "$ERROR_LOG"); then
                echo -e "${YELLOW}$pkg${ENDCOLOR}${LIGHTBLUE} installed successfully.${ENDCOLOR}"
            else
                echo -e "${YELLOW}$pkg${ENDCOLOR}${RED} failed to install. Check ${YELLOW}RiceError.log${ENDCOLOR}"
                log_error "Failed to install AUR package: $pkg"
            fi
            sleep 1
        else
            echo -e "${YELLOW}$pkg${GREEN} is already installed.${ENDCOLOR}"
            sleep 1
        fi
    done
}

# Backup user files
backup_files() {
    echo -e "${CYAN}Backing up files to $backup_folder${ENDCOLOR}"
    rsync -aAEHSXxr --delete --exclude=".cache/mozilla/*" ~/.[^.]* "$backup_folder" || {
        echo -e "${RED}Backup failed!${ENDCOLOR}"
        log_error "Backup failed"
        exit 1
    }
    echo -e "${ORANGE}Backup completed!${ENDCOLOR}"
}

# Install dotfiles
install_dotfiles() {
    echo -e "${CYAN}Installing dotfiles...${ENDCOLOR}"
    cp -rf "$current_dir"/user/.* "$home_dir"
    
    # Install GRUB theme if not present
    if [ ! -d /usr/share/grub/themes/catppuccin-mocha-grub-theme ]; then
        sudo cp -rf "$current_dir"/grub_themes/catppuccin-mocha-grub-theme /usr/share/grub/themes/ >/dev/null 2> >(tee -a "$ERROR_LOG")
    fi

    # Install additional packages if folder exists
    if [ -d "$current_dir"/pkgs_virOS ]; then
        echo -e "${CYAN}Additional packages folder found${ENDCOLOR}"
        sudo rm -rf /usr/share/icons/*
        sudo pacman -U "$current_dir"/pkgs_virOS/*.zst --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
    else
        echo -e "${YELLOW}Downloading additional packages...${ENDCOLOR}"
        cd "$current_dir" || exit
        gdown --folder 19SlCmblUJts_I5dlAwd2C3tq7q2-wLbS || {
            echo -e "${RED}Failed to download additional packages${ENDCOLOR}"
            log_error "Failed to download additional packages"
        }
    fi
    
    # Copy binary files
    sudo cp -rf "$current_dir"/user/.bin/virlock /usr/bin
    echo -e "${GREEN}Dotfiles installed successfully!${ENDCOLOR}"
}

# Configure SDDM
configure_sddm() {
    # Remove lightdm if installed
    if [ -f /usr/bin/lightdm ]; then
        sudo systemctl disable lightdm.service >/dev/null 2> >(tee -a "$ERROR_LOG")
        sudo pacman -Rdd lightdm lightdm-gtk-greeter --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
    fi

    # Install and configure SDDM
    if [ ! -d /etc/sddm.conf.d/ ]; then
        sudo pacman -S sddm --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
    fi
    
    sudo cp -rf "$current_dir"/sddm/sddm.conf.d /etc/ >/dev/null 2> >(tee -a "$ERROR_LOG")
    sudo cp -rf "$current_dir"/sddm/catppuccin-mocha /usr/share/sddm/themes >/dev/null 2> >(tee -a "$ERROR_LOG")
    sudo systemctl enable sddm.service >/dev/null 2> >(tee -a "$ERROR_LOG")
    echo -e "${LIGHTCYAN}SDDM configured successfully!${ENDCOLOR}"
}

# Configure GRUB theme
configure_grub() {
    local GRUB_THEME_DIR="/usr/share/grub/themes"
    local grub_theme="catppuccin-mocha-grub-theme"

    if [ ! -d "$GRUB_THEME_DIR"/"$grub_theme" ]; then
        sudo cp -rf "$current_dir"/grub_themes/"$grub_theme" /usr/share/grub/themes/
    fi

    if [ -f /etc/default/grub ]; then
        sudo sed -i "s|.*GRUB_THEME=.*|GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"|" /etc/default/grub >/dev/null 2> >(tee -a "$ERROR_LOG")
    else
        echo "GRUB_THEME=\"${GRUB_THEME_DIR}/${grub_theme}/theme.txt\"" | sudo tee /etc/default/grub
    fi
    
    sudo grub-mkconfig -o /boot/grub/grub.cfg >/dev/null 2> >(tee -a "$ERROR_LOG")
    echo -e "${LIGHTCYAN}GRUB configured successfully!${ENDCOLOR}"
}

# Configure Firefox theme
configure_firefox() {
    # Detect Firefox profile paths
    if grep -q '\[Profile[^0]\]' ~/.mozilla/firefox/profiles.ini; then 
        PROFPATH_0=$(grep -A 10 "\[Profile0\]" ~/.mozilla/firefox/profiles.ini | sed '1d' | grep -m 1 -B 10 "\[" | grep "Path=" | sed -e 's/Path=//')
    elif grep -q '\[Profile[^1]\]' ~/.mozilla/firefox/profiles.ini; then 
        PROFPATH_1=$(grep -A 10 "\[Profile1\]" ~/.mozilla/firefox/profiles.ini | sed '1d' | grep -m 1 -B 10 "\[" | grep "Path=" | sed -e 's/Path=//')
    fi

    # Copy Firefox theme and extensions
    cp -rf "$current_dir"/firefox/userstyles ~/.mozilla/firefox/

    if [ -n "$PROFPATH_0" ] && [ -d ~/.mozilla/firefox/"$PROFPATH_0" ]; then
        cp -R "$current_dir"/firefox/FoxThemes/* ~/.mozilla/firefox/"$PROFPATH_0"
        echo -e "${GREEN}Firefox theme installed in ${YELLOW}$PROFPATH_0${ENDCOLOR}"
        
        if [ -d ~/.mozilla/firefox/"$PROFPATH_0"/extensions ]; then
            cp -R "$current_dir"/firefox/extensions/* ~/.mozilla/firefox/"$PROFPATH_0"/extensions
            echo -e "${GREEN}Firefox extensions installed in ${YELLOW}$PROFPATH_0${ENDCOLOR}"
        fi
    elif [ -n "$PROFPATH_1" ] && [ -d ~/.mozilla/firefox/"$PROFPATH_1" ]; then
        cp -R "$current_dir"/firefox/FoxThemes/* ~/.mozilla/firefox/"$PROFPATH_1"
        echo -e "${GREEN}Firefox theme installed in ${YELLOW}$PROFPATH_1${ENDCOLOR}"
        
        if [ -d ~/.mozilla/firefox/"$PROFPATH_1"/extensions ]; then
            cp -R "$current_dir"/firefox/extensions/* ~/.mozilla/firefox/"$PROFPATH_1"/extensions
            echo -e "${GREEN}Firefox extensions installed in ${YELLOW}$PROFPATH_1${ENDCOLOR}"
        fi
    else
        echo -e "${RED}Firefox theme/extensions not installed! Install manually!${ENDCOLOR}"
        log_error "Failed to install Firefox theme/extensions"
    fi
}

# Detect GPU and configure polybar accordingly
detect_gpu() {
    local scrDir="$(dirname "$(realpath "$0")")"
    readarray -t dGPU < <(lspci -k | grep -E "(VGA|3D)" | awk -F ': ' '{print $NF}')
    
    if grep -iq nvidia <<< "${dGPU[@]}"; then
        rm -rf "$home_dir/.config/i3/rices/catppuccin-mocha/config.ini"
        cp "$current_dir"/polybar_rices/nvidia/config.ini "$home_dir/.config/i3/rices/catppuccin-mocha/"
        echo -e "${ORANGE}NVIDIA GPU detected!${ENDCOLOR}"
    else
        rm -rf "$home_dir/.config/i3/rices/catppuccin-mocha/config.ini"
        cp "$current_dir"/polybar_rices/not_nvidia/config.ini "$home_dir/.config/i3/rices/catppuccin-mocha/"
        echo -e "${CYAN}No NVIDIA GPU detected!${ENDCOLOR}"
    fi
}

# Configure libvirt group and MPD service
configure_services() {
    # Configure libvirt group
    local VIRTGROUP="libvirt"
    if ! grep -q $VIRTGROUP /etc/group; then
        sudo groupadd libvirt
        sudo usermod -a -G libvirt "$(whoami)"
        sudo systemctl enable --now libvirtd
        echo -e "${GREEN}libvirt group configured!${ENDCOLOR}"
    else
        echo -e "${GREEN}libvirt group already exists!${ENDCOLOR}"
    fi

    # Configure MPD service
    if systemctl is-enabled --quiet mpd.service; then
        echo -e "${RED}Disabling${ENDCOLOR} ${GREEN}global MPD service!${ENDCOLOR}"
        sudo systemctl disable --now mpd.service >/dev/null 2> >(tee -a "$ERROR_LOG") || {
            echo -e "${RED}Failed to disable global MPD service!${ENDCOLOR}"
            log_error "Failed to disable global MPD service"
        }
    fi

    echo -e "${ORANGE}Enabling user-level MPD service!${ENDCOLOR}"
    systemctl --user enable --now mpd.service >/dev/null 2> >(tee -a "$ERROR_LOG") || {
        echo -e "${RED}Failed to enable user MPD service! Check ${YELLOW}RiceError.log${ENDCOLOR}"
        log_error "Failed to enable user MPD service"
    }
}

# Setup wallpaper changer service
setup_wallpaper_changer() {
    local SERVICE_FILES=("wallpaper-changer.service" "wallpaper-changer.timer")
    local TARGET_DIR="$HOME/.config/systemd/user"

    mkdir -p "$TARGET_DIR" || {
        echo -e "${RED}Failed to create $TARGET_DIR!${ENDCOLOR}"
        log_error "Failed to create directory: $TARGET_DIR"
        exit 1
    }

    for file in "${SERVICE_FILES[@]}"; do
        if [[ -f "$current_dir/systemd/user/$file" ]]; then
            cp -v "$current_dir/systemd/user/$file" "$TARGET_DIR/" || {
                echo -e "${RED}Failed to copy $file to $TARGET_DIR!${ENDCOLOR}"
                log_error "Failed to copy: $file"
                exit 1
            }
            chmod 644 "$TARGET_DIR/$file"
        else
            echo -e "${RED}Error: $current_dir/systemd/user/$file not found!${ENDCOLOR}"
            log_error "Source file not found: $file"
            exit 1
        fi
    done

    systemctl --user daemon-reload || {
        echo -e "${RED}Failed to reload systemd user daemon.${ENDCOLOR}"
        log_error "Failed to reload systemd user daemon"
        exit 1
    }

    systemctl --user enable --now wallpaper-changer.timer || {
        echo -e "${RED}Failed to enable wallpaper-changer.timer.${ENDCOLOR}"
        log_error "Failed to enable wallpaper-changer.timer"
        exit 1
    }
    
    echo -e "${GREEN}Wallpaper changer service configured!${ENDCOLOR}"
}

# Change shell to zsh if not already
change_shell_to_zsh() {
    if [[ $SHELL != "/usr/bin/zsh" ]]; then
        echo -e "${YELLOW}Changing shell to zsh...${ENDCOLOR}"
        chsh -s /usr/bin/zsh 2> >(tee -a "$ERROR_LOG") || {
            echo -e "${RED}Failed to change shell to zsh! Check ${YELLOW}RiceError.log${ENDCOLOR}"
            log_error "Failed to change shell to zsh"
        }
    else
        echo -e "${GREEN}Shell is already zsh!${ENDCOLOR}"
    fi
}

# Prompt for reboot
prompt_reboot() {
    echo -e "${YELLOW}Installation complete! A reboot is recommended.${ENDCOLOR}"
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
                echo -e "${GREEN}OK, remember to reboot later!${ENDCOLOR}"
                break
                ;;
            * )
                echo -e "${YELLOW}Please answer yes or no!${ENDCOLOR}"
                ;;
        esac
    done
}

# Package lists
official_packages=(base base-devel sof-firmware alacritty brightnessctl dunst bottom imagemagick \
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

aur_packages=(cava tor-browser-bin ymuse-git zscroll-git eww-git musnify-mpd gnome-icon-theme zsh-theme-powerlevel10k powerline-fonts-git\
              catppuccin-cursors-mocha ttf-meslo-nerd-font-powerlevel10k ytdlp-gui oh-my-zsh-git oh-my-posh-bin autotiling gtkhash-thunar \
              i3lock-color gdown kazam kodi-addon-pvr-iptvsimple hypnotix)

##-----------------
#-- Main Script
##-----------------

# Check if running as root
if [ "$(id -u)" = 0 ]; then
    echo -e "${LIGHTBLUE}This script MUST NOT be run as root.${ENDCOLOR}"
    exit 1
fi

# Initialize Firefox settings
initialize_firefox

# Display welcome message
display_logo "$PURPLE" "VIROS DOTS"
echo -e "${YELLOW}This script checks for required packages and installs them if needed.${ENDCOLOR}"

# Confirm continuation
while true; do
    read -rp "Continue? [y/N]: " yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done
clear

# Remove unwanted packages
[ -f /usr/bin/i3lock ] && sudo pacman -R i3lock --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")
[ -f /usr/bin/zenity ] && sudo pacman -R zenity --noconfirm >/dev/null 2> >(tee -a "$ERROR_LOG")

# Install official packages
install_official_packages "${official_packages[@]}"
sleep 3
clear

# Create user directories if needed
[ ! -e "$HOME/.config/user-dirs.dirs" ] && xdg-user-dirs-update

# Install paru if not present
display_logo "$ORANGE" "PARU INSTALL"
if ! command -v paru >/dev/null; then
    echo -e "${YELLOW}Installing paru...${ENDCOLOR}"
    {
        cd "$HOME" || exit
        git clone https://aur.archlinux.org/paru-bin.git
        cd paru-bin || exit
        makepkg -si --noconfirm 
    } || {
        echo -e "${RED}Failed to install Paru. Install manually!${ENDCOLOR}"
        log_error "Failed to install Paru"
        exit 1
    }
fi

# Install wallpapers
wallpaper_install() {
    local wallpaper_src="/etc/skel/.config/i3/rices/catppuccin-mocha/walls/"
    local wallpaper_dest="$HOME/.config/i3/rices/catppuccin-mocha/"

    if [ -d "$wallpaper_src" ]; then
        mkdir -p "$wallpaper_dest"  # Создать целевую директорию, если её нет
        cp -r "$wallpaper_src" "$wallpaper_dest"  # Копировать без sudo
        chown -R "$usr:$usr" "$wallpaper_dest"   # Установить владельца (если нужно)
        echo -e "${GREEN}Wallpapers copied to $wallpaper_dest${ENDCOLOR}"
    else
        echo -e "${RED}Source wallpapers not found in $wallpaper_src${ENDCOLOR}"
        log_error "Wallpaper source directory not found: $wallpaper_src"
    fi
}

[ ! -f /usr/bin/paru ] && { echo -e "${RED}Paru not installed! Exiting...${ENDCOLOR}"; exit 1; }
sleep 3
clear

# Install AUR packages
install_aur_packages "${aur_packages[@]}"
sleep 3
clear

# Backup files
display_logo "$GREEN" "BACKUP"
backup_files
sleep 2
clear

# Clean existing configs
for del in polybar rofi picom.conf; do
    rm -rf ~/.config/$del
done

# Install dotfiles
display_logo "$GREEN" "INSTALL DOTFILES"
install_dotfiles
sleep 2

# Update font cache
fc-cache -rv >/dev/null 2>&1

# Configure Thunar
xfconf-query -c thunar -p /misc-open-new-windows-in-split-view -n -t bool -s true
clear

# Configure SDDM
display_logo "$GREEN" "SDDM"
configure_sddm
sleep 3
clear

# Configure GRUB
display_logo "$GREEN" "GRUB"
configure_grub
sleep 3
clear

# Configure Firefox
display_logo "$GREEN" "FIREFOX"
configure_firefox
sleep 3
clear

# Detect GPU and configure polybar
display_logo "$GREEN" "NVIDIA"
detect_gpu
sleep 3
clear

# Configure services
display_logo "$GREEN" "MPD&LIBVIRT"
configure_services
sleep 3
clear

display_logo "$ORANGE" "WALLPAPERS"
# Setup wallpaper changer
wallpaper_install
setup_wallpaper_changer

# Change shell to zsh
display_logo "$GREEN" "ZSH install"
change_shell_to_zsh
sleep 3
clear

# Prompt for reboot
display_logo "$GREEN" "REBOOT"
prompt_reboot