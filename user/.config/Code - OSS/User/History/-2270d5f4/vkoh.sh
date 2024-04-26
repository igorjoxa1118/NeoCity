#!/bin/bash

## calamares shellprocess_system.conf
# run no chroot
# add config iso > system

chroot_path=$(cat /tmp/chroot_path.tmp)
[[ -d $chroot_path ]] || exit

cp -rf /var/log/ctlos.log ${chroot_path}/var/log

mkdir -p ${chroot_path}/etc/default
cp -rf /etc/default/grub ${chroot_path}/etc/default
cp -rf /etc/grub.d ${chroot_path}/etc
cp -rf /etc/default/useradd ${chroot_path}/etc/default

cp -rf /etc/modprobe.d ${chroot_path}/etc
cp -rf /etc/polkit-1 ${chroot_path}/etc
cp -rf /etc/machine-id ${chroot_path}/etc

mkdir -p ${chroot_path}/etc/pacman.d/hooks
cp -rf /etc/pacman.d/hooks/issue.hook ${chroot_path}/etc/pacman.d/hooks
cp -rf /etc/pacman.d/hooks/lsb-release.hook ${chroot_path}/etc/pacman.d/hooks
cp -rf /etc/pacman.d/hooks/mirrors.hook ${chroot_path}/etc/pacman.d/hooks
cp -rf /etc/pacman.d/hooks/os-release.hook ${chroot_path}/etc/pacman.d/hooks

cp -rf /etc/sysctl.d ${chroot_path}/etc
cp -rf /etc/udev/rules.d ${chroot_path}/etc/udev
cp -rf /etc/X11/xorg.conf.d ${chroot_path}/etc/X11
cp -rf /etc/xdg/reflector ${chroot_path}/etc/xdg
cp -rf /etc/motd ${chroot_path}/etc
cp -rf /etc/ntp.conf ${chroot_path}/etc
cp -rf /etc/sddm.conf.d ${chroot_path}/etc

cp -rf /etc/pamac.conf ${chroot_path}/etc
cp -rf /etc/pacman.conf ${chroot_path}/etc
# sed -i "/\[chaotic-aur\]/,+2d" ${chroot_path}/etc/pacman.conf

cp -rf /etc/systemd/journald.conf.d ${chroot_path}/etc/systemd
cp -rf /etc/systemd/logind.conf.d ${chroot_path}/etc/systemd
cp -rf /etc/systemd/network ${chroot_path}/etc/systemd

# cp -rf /etc/systemd/system ${chroot_path}/etc/systemd
mkdir -p ${chroot_path}/etc/systemd/system
cp -rf /etc/systemd/system/choose-mirror.service ${chroot_path}/etc/systemd/system
cp -rf /etc/systemd/system/pacman-init.service ${chroot_path}/etc/systemd/system
cp -rf /etc/systemd/system/etc-pacman.d-gnupg.mount ${chroot_path}/etc/systemd/system
cp -rf /etc/systemd/system/default.service ${chroot_path}/etc/systemd/system
cp -rf /etc/systemd/system/ctlos-system.service ${chroot_path}/etc/systemd/system

rm ${chroot_path}/etc/systemd/system/display-manager.service

cp -rf /root/.config ${chroot_path}/root
cp -rf /root/.gtkrc-2.0 ${chroot_path}/root

cp -rf /usr/local/bin/cleaner.sh ${chroot_path}/usr/local/bin
cp -rf /usr/local/bin/multilock.sh ${chroot_path}/usr/local/bin
cp -rf /usr/local/bin/show_desktop ${chroot_path}/usr/local/bin
cp -rf /usr/local/bin/ctlos-system ${chroot_path}/usr/local/bin

cp -rf /usr/share/icons/default ${chroot_path}/usr/share/icons
cp -rf /usr/share/icons/linebit ${chroot_path}/usr/share/icons

echo "FONT=cyr-sun16" >> ${chroot_path}/etc/vconsole.conf

rm /usr/local/bin/system.sh