#!/bin/bash

local_repo=${PWD}
echo $local_repo
repo_vir0S=cretm@cloud.vir0S.ru:/home/cretm/app/cloud.vir0S.ru/vir0S_repo/
repo_osdn=creio@storage.osdn.net:/storage/groups/c/ct/vir0S/vir0S_repo/
repo_keybase=/run/user/1000/keybase/kbfs/public/cvc/vir0S_repo/

_keybase() {
  srv_keybase="$(systemctl status --user kbfs | grep -i running 2>/dev/null || echo '')"
  if [[ "$srv_keybase" ]]; then
    rsync -cauvCLP --delete-excluded --delete --exclude={"build",".git*",".*ignore"} "$local_repo"/ "$repo_keybase"
  else
    systemctl start --user kbfs
    sleep 4
    echo "systemctl start --user kbfs done"
    rsync -cauvCLP --delete-excluded --delete --exclude={"build",".git*",".*ignore"} "$local_repo"/ "$repo_keybase"
  fi
  # if read -re -p "stop keybase user service? [Y/n]: " ans && [[ $ans == 'n' || $ans == 'N' ]]; then
  #   echo "skip stop kbfs"
  # else
  #   systemctl stop --user kbfs
  #   echo "stop kbfs done"
  # fi
  echo "rsync keybase repo"
}

if [ "$1" = "-add" ]; then
  # repo-add -s -v -n -R vir0S_repo.db.tar.zst *.pkg.tar.xz
  # repo-add -n -R vir0S_repo.db.tar.zst *.pkg.tar.{xz,zst}
  repo-add -n -R -q vir0S_repo.db.tar.zst *.pkg.tar.zst 2>/dev/null;
  rm vir0S_repo.{db,files}
  cp -f vir0S_repo.db.tar.zst vir0S_repo.db
  cp -f vir0S_repo.files.tar.zst vir0S_repo.files
  ##optional-remove for old repo.db##
  # rm *gz.old{,.sig}
echo "Repo Up"
elif [ "$1" = "-clean" ]; then
  rm vir0S_repo*
  echo "Repo clean"
elif [ "$1" = "-o" ]; then
  rsync -cauvCLP --delete-excluded --delete "$local_repo" "$repo_osdn"
  echo "rsync osdn repo"
# systemctl --user start kbfs
elif [ "$1" = "-sync" ]; then
  _keybase
  rsync -cauvCLP --delete-excluded --delete "$local_repo" "$repo_osdn"
  echo "rsync all repo"
# systemctl --user start kbfs
elif [ "$1" = "-k" ]; then
  _keybase
elif [ "$1" = "-all" ]; then
  repo-add -n -R -q vir0S_repo.db.tar.zst *.pkg.tar.zst
  rm vir0S_repo.{db,files}
  cp -f vir0S_repo.db.tar.zst vir0S_repo.db
  cp -f vir0S_repo.files.tar.zst vir0S_repo.files
  _keybase
  # rsync -cauvCLP --delete-excluded --delete "$local_repo" "$repo_vir0S"
  rsync -cauvCLP --delete-excluded --delete "$local_repo" "$repo_osdn"
  echo "add pkg, rsync all repo"
else
  repo-add -n -R vir0S_repo.db.tar.zst *.pkg.tar.zst
  rm vir0S_repo.{db,files}
  cp -f vir0S_repo.db.tar.zst vir0S_repo.db
  cp -f vir0S_repo.files.tar.zst vir0S_repo.files
  echo "Done repo-add pkg"
fi

## sync vir0S-aur repo
aur_vir0S=cretm@cloud.vir0S.ru:/home/cretm/app/cloud.vir0S.ru/vir0S-aur/
aur_keybase=/run/user/1000/keybase/kbfs/public/cvc/vir0S-aur/

if [ "$1" = "-aur" ]; then
  srv_keybase="$(systemctl status --user kbfs | grep -i running 2>/dev/null || echo '')"
  if [[ "$srv_keybase" ]]; then
    rsync -cauvCLP --delete-excluded --delete "$aur_vir0S" "$aur_keybase"
  fi
  echo "sync aur"
fi