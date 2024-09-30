#!/usr/bin/bash
set -x

DIR="$HOME"

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

for pkges in "$HOME/smb.conf"
do
if [ ! -f /etc/smb.conf ]; then
    sudo touch /etc/$pkges
    sudo cat $DIR/smb.conf > /etc/smb.conf
else
    echo "File exist!"
fi
done

function_log() {
echo /mjt > /var/log/samba/%m.log
log file = /var/log/samba/%m.log
}
sleep 1

function_start_service() {
   sudo systemctl start smb.service
   sudo systemctl enable smb.service
   sudo systemctl start nmb.service
   sudo systemctl enable nmb.service
}

if function_log; then
   function_start_service
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
   read -p "What user you want??: " user
   sudo smbpasswd -a $user
   sudo groupadd -r sambauser
   read -p "What directory you want share??: " share
   sudo chown $user:sambauser $share
   sudo chmod -R 770 $share
   sed -i "s/User1/${user}/g" /etc/smb.conf
   sed -i "s//srv/myfiles/${share}/g" /etc/smb.conf
   sudo gpasswd sambauser -a $user
   sudo systemctl restart smb.service
   sudo systemctl restart nmb.service
fi
  