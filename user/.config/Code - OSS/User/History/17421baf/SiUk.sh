#!/usr/bin/bash

smb_active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')
nmb_active=$(sudo systemctl status nmb | grep '(running)' | awk '{print $3}')

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