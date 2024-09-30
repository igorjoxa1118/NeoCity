#!/bin/bash

### calamares module baseinstall

chroot_path=$(cat /tmp/chroot_path.tmp)
[[ -d $chroot_path ]] || exit

exec > >(tee /var/log/ctlos.log) 2>&1

pacman -S reflector --noconfirm --needed
reflector -a 12 -l 5 -p https,http --sort rate --save /etc/pacman.d/mirrorlist
pacman -Syy archlinux-keyring --noconfirm

if [[ $(command -v pacstrap) ]]; then
  pacman -S arch-install-scripts --noconfirm
fi

if [[ ! -f "/usr/bin/pacstrap.sh" ]]; then
# sed -e '/chroot_add_mount proc/d' \
#   -e '/chroot_add_mount sys/d' \
#   -e '/ignore_error chroot_maybe_add_mount/d' \
#   -e '/chroot_add_mount udev/d' \
#   -e '/chroot_add_mount devpts/d' \
#   -e '/chroot_add_mount shm/d' \
#   -e '/chroot_add_mount run/d' \
#   -e '/chroot_add_mount tmp/d' \
#   -e '/efivarfs \"/d' /usr/bin/pacstrap >/usr/bin/pacstrap.sh
curl -s -Lo /usr/bin/pacstrap.sh https://raw.githubusercontent.com/ctlos/ctlos-sh/master/pacstrap_bak
chmod +x /usr/bin/pacstrap.sh
fi

_vbox() {
  result=$(systemd-detect-virt)
  if [ $result = "oracle" ]; then
    vbox_pkgs="virtualbox-guest-utils"
  elif [ $result = "vmware" ]; then
    vbox_pkgs=""
  else
    vbox_pkgs=""
  fi
}
_vbox

PKGS=(
base sudo grub reflector lsb-release nano iwd haveged
gnu-netcat rsync zsh
)

/usr/bin/pacstrap.sh ${chroot_path} ${PKGS[@]} $vbox_pkgs

curl -s -o ${chroot_path}/usr/local/bin/settings.sh -L https://raw.githubusercontent.com/ctlos/ctlos-sh/master/settings.sh
chmod +x ${chroot_path}/usr/local/bin/settings.sh

curl -s -o ${chroot_path}/usr/local/bin/strap.sh -L https://raw.githubusercontent.com/ctlos/ctlos-sh/master/strap.sh
chmod +x ${chroot_path}/usr/local/bin/strap.sh

curl -s -o /usr/local/bin/system.sh -L https://raw.githubusercontent.com/ctlos/ctlos-sh/master/system.sh
chmod +x /usr/local/bin/system.sh

curl -s -o ${chroot_path}/usr/local/bin/postinstall.sh -L https://raw.githubusercontent.com/ctlos/ctlos-sh/master/postinstall.sh
chmod +x ${chroot_path}/usr/local/bin/postinstall.sh

# copy to chroot
mkdir -p ${chroot_path}/etc/pacman.d
cp -rfv /etc/pacman.d/*mirrorlist ${chroot_path}/etc/pacman.d

echo "==== Done pacstrap.sh ===="
