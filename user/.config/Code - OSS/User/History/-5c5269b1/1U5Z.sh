#!/usr/bin/bash


DIR=""$HOME"/Загрузки/repository/sources_test/samba_config"

if [ "$(id -u)" = 0 ]; then
    echo -e "${LIGHTBLUE}This script MUST NOT be run as root user."
    exit 1
fi

while true; do
	read -rp "Do you wish to continue? [y/N]: " yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

dependencias=(samba smbclient)

is_installed() {
  pacman -Qi "$1" &> /dev/null
  return $?
}

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

if [ ! -f /etc/smb.conf ]; then
    cd /etc/ || exit
    touch /etc/smb2.conf
    cat $DIR/smb.conf > "$HOME"/Загрузки/repository/sources_test/samba_config/test_for_touch/smb2.conf
else
    echo "File exist!"
fi