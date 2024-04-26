#!/usr/bin/bash
set -x

DIR=""$HOME"/Загрузки/repository/sources_test/samba_config"

#if [ "$(id -u)" = 0 ]; then
#    echo -e "${LIGHTBLUE}This script MUST NOT be run as root user."
#    exit 1
#fi

while true; do
	read -rp "Do you wish to continue? [y/N]: " yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit;;
			* ) printf " Error: just write 'y' or 'n'\n\n";;
		esac
    done
clear

dependencias=(samba smbclient testparm log)

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
   sudo systemctl start smb
   sudo systemctl enable smb
   sudo systemctl start nmb
   sudo systemctl enable nmb
fi

smb_active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')
nmb_active=$(sudo systemctl status nmb | grep '(running)' | awk '{print $3}')

active_func() {
if [ "$smb_active" = '(running)' ]; then
  echo "$smb_active запущен"
  else
    echo "$smb_active не запущен"
fi

if [ "$nmb_active" = '(running)' ]; then
  echo "$nmb_active запущен"
  else
    echo "$nmb_active не запущен"
fi
}


if [ active_func ]; then
   read -p "What user you want??: "user
   sudo smbpasswd -a $user
   sudo groupadd -r sambauser
   read -p "What directory you want share??: "share
   sudo chown $user:sambauser $share
   sudo chmod -R 770 $share
   sed -i "s/User1/${user}/g" /etc/smb.conf
   sed -i "s//srv/myfiles/${share}/g" /etc/smb.conf
   sudo gpasswd sambauser -a $user
   sudo systemctl restart smb
   sudo systemctl restart nmb
fi
  