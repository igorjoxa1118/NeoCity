#!/usr/bin/bash

active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')
active2="(running)"

if [ "$active" = $active2 ]; then
  echo "$active запущен"
  else
    echo "$active не запущен"
fi