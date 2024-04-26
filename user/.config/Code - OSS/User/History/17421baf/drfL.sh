#!/usr/bin/bash

smb_active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')
nmb_active=$()

if [ "$smb_active" = '(running)' ]; then
  echo "$smb_active Запущен"
  elif [ "$nmb_active" = '(running)' ]; then
    echo "$nmb_active Запущен"
  else
    echo "$active не запущен"
fi