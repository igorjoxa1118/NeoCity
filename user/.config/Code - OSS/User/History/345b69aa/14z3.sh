#!/bin/bash

repo_dir="$HOME/Tokio_night"

if [ -f /usr/bin/firefox]; then
firefox
sleep 5
killall firefox
fi

for ff_themes in $repo_dir/firefox/*; do
  cp -R "${ff_themes}" ~/.mozilla/firefox/*.default-release/
  if [ $? -eq 0 ]; then
	printf "%s%s%s folder copied succesfully!%s\n" "${BLD}" "${CGR}" "${ff_themes}" "${CNC}"
	sleep 1
  else
	printf "%s%s%s failed to been copied, you must copy it manually%s\n" "${BLD}" "${CRE}" "${ff_themes}" "${CNC}"
	sleep 1
  fi
done

sleep 5
clear