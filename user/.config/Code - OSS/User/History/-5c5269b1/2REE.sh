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
    cat $DIR/smb.conf > /etc/smb.conf
else
    echo "File exist!"
fi

function_log() {
echo /mjt > /var/log/samba/%m.log
if [ $(log file = /var/log/samba/%m.log) ]; then
sleep 1
echo "Ok"
else
echo "Somting wrong!"
exit 1
fi
}
sleep 1
clear

if function_log; then
sudo testparm
sleep 5
fi

