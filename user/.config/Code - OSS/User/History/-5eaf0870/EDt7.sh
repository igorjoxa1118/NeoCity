#!/bin/bash

## calamares shellprocess_postinstall.conf
# run chroot

clean_post() {
  local files_rm=(
    /etc/systemd/system/multi-user.target.wants/{choose-mirror.service,pacman-init.service,reflector.service}
  )
  local i
  for i in ${files_rm[*]}; do rm -rf $i; done
}

enable_dm() {
  rm /etc/systemd/system/display-manager.service
  [[ $(pacman -Qs sddm) ]] && systemctl enable sddm
  [[ $(pacman -Qs lightdm) ]] && systemctl enable lightdm
  [[ $(pacman -Qs lxdm) ]] && systemctl enable lxdm
  [[ $(pacman -Qs gdm) ]] && systemctl enable gdm
  # systemctl set-default graphical.target
}

clean_post
enable_dm

rm /usr/local/bin/postinstall.sh