#!/usr/bin/bash

smb_active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')
nmb_active=$(sudo systemctl status nmb | grep '(running)' | awk '{print $3}')

if [ "$active" = '(running)' ]; then
  echo "$active запущен"
  else
    echo "$active не запущен"
fi