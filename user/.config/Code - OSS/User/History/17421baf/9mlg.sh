#!/usr/bin/bash

active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')
active2="(running)"

if [ "$active" = '(running)' ]; then
  echo "$active запущен"
  else
    echo "$active не запущен"
fi