#!/usr/bin/bash

active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')

if [ ! -z "$active" ]; then
  echo "$active запущен"
  else
    echo "$active не запущен"
fi