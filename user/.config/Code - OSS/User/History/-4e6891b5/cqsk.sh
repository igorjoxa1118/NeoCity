#!/bin/sh

# fork blackarch strap.sh

baseurl=https://raw.githubusercontent.com/ctlos/ctlos_repo/master/x86_64
keyring_pkg=ctlos-keyring-stable-2-x86_64
mirror_pkg=ctlos-mirrorlist-stable-1-x86_64
MIRROR_F="ctlos-mirrorlist"
MIRROR_AUR="ctlos-aur"

err() {
  echo >&2 "$(tput bold; tput setaf 1)[-] ERROR: ${*}$(tput sgr0)"
  exit 1337
}
warn() {
  echo >&2 "$(tput bold; tput setaf 1)[!] WARNING: ${*}$(tput sgr0)"
}
msg() {
  echo "$(tput bold; tput setaf 2)[+] ${*}$(tput sgr0)"
}
check_priv() {
  if [ "$(id -u)" -ne 0 ]; then
    err "you must be root"
  fi
}

make_tmp_dir() {
  tmp="$(mktemp -d /tmp/ctlos_strap.XXXXXXXX)"

  trap 'rm -rf $tmp' EXIT

  cd "$tmp" || err "Could not enter directory $tmp"
}

check_internet() {
  tool='curl'
  tool_opts='-s --connect-timeout 8'

  if ! $tool $tool_opts https://google.com/ > /dev/null 2>&1; then
    err "You don't have an Internet connection!"
  fi

  return $SUCCESS
}

# retrieve the Ctlos Linux keyring
fetch_keyring() {
  curl -s -O $baseurl/$keyring_pkg.pkg.tar.zst{,.sig}
}

# verify the keyring signature
verify_keyring() {
  if [ -f "/usr/share/pacman/keyrings/ctlos.gpg" ]; then
    msg 'gpg key installed /usr/share/pacman/keyrings/ctlos.gpg'
  else
    curl -s -Lo /usr/share/pacman/keyrings/ctlos.gpg git.io/ctlos.gpg
    pacman-key --add /usr/share/pacman/keyrings/ctlos.gpg
    # pacman-key --keyserver keys.gnupg.net --recv-keys 98F76D97B786E6A3
    # pacman-key --recv-keys 98F76D97B786E6A3
    pacman-key --lsign-key 98F76D97B786E6A3
  fi
}

# delete the signature files
delete_signature() {
  if [ -f "$keyring_pkg.pkg.tar.zst.sig" ]; then
    rm $keyring_pkg.pkg.tar.zst.sig
  fi
}

# make sure /etc/pacman.d/gnupg is usable
check_pacman_gnupg() {
  pacman-key --init
}

# install the keyring
install_keyring() {
  if ! pacman --config /dev/null --noconfirm --overwrite='*' \
    -U $keyring_pkg.pkg.tar.zst ; then
    err 'keyring installation failed'
  fi
  pacman-key --populate
}

install_mirrors() {
  curl -s -O $baseurl/$mirror_pkg.pkg.tar.zst{,.sig}

  if [ -f "$mirror_pkg.pkg.tar.zst.sig" ]; then
    rm $mirror_pkg.pkg.tar.zst.sig
  fi

  if ! pacman --config /dev/null --noconfirm --overwrite='*' \
    -U $mirror_pkg.pkg.tar.zst ; then
    err 'mirrors installation failed'
  fi
}

# update pacman.conf
update_pacman_conf() {
  # delete ctlos related entries if existing
  sed -i '/ctlos_repo/{N;d}' /etc/pacman.conf

  cat >> "/etc/pacman.conf" << EOF

[ctlos_repo]
Include = /etc/pacman.d/$MIRROR_F
EOF
}
add_ctlos_aur() {
  sed -i '/ctlos-aur/,+2d' /etc/pacman.conf
  cat >> "/etc/pacman.conf" << EOF

[ctlos-aur]
SigLevel = Optional TrustAll
Include = /etc/pacman.d/$MIRROR_F
EOF
}

# synchronize and update
pacman_update() {
  if pacman -Syy; then
    return $SUCCESS
  fi

  warn "Synchronizing pacman has failed. Please try manually: pacman -Syy"

  return $FAILURE
}

pacman_upgrade() {
  echo 'perform full system upgrade? (pacman -Su) [Yn]:'
  read conf < /dev/tty
  case "$conf" in
    ''|y|Y) pacman -Su ;;
    n|N) warn 'some ctlos packages may not work without an up-to-date system.' ;;
  esac
}

# setup ctlos linux
ctlos_setup() {
  check_priv
  msg 'installing ctlos keyring...'
  make_tmp_dir
  check_internet
  fetch_keyring
  verify_keyring
  delete_signature
  check_pacman_gnupg
  install_keyring
  echo
  msg 'keyring installed successfully'
  install_mirrors
  echo
  msg 'mirrorlist installed successfully'
  # check if pacman.conf has already a mirror
  if ! grep -q "\[ctlos_repo\]" /etc/pacman.conf; then
    msg 'updating pacman.conf'
    update_pacman_conf
  fi
  if ! grep -q "\[ctlos-aur\]" /etc/pacman.conf; then
    msg 'add ctlos-aur pacman.conf'
    add_ctlos_aur
  fi
  msg 'updating package databases'
  pacman_update
  # pacman_upgrade
  msg 'Ctlos Linux repo is ready!'
}

if [ "$1" != "-an" ]; then
  ctlos_setup
fi

## archinstall config
if [ "$1" = "-a" -o "$1" = "-an" ]; then
curl -s -LO kutt.it/config-json
curl -s -LO kutt.it/disk-json

if ls | grep "json"; then
cat <<EOF

nano /root/config-json
nano /root/disk-json

https://archinstall.readthedocs.io/installing/guided.html
archinstall --help

archinstall --config /root/config-json --disk_layouts=/root/disk-json
EOF
fi
fi