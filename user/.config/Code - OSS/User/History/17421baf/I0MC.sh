#!/usr/bin/bash

active=$(sudo systemctl status smb | grep '(running)' | awk '{print $3}')

if [ -z "$active" ]; then
  echo "Сервез активен и запущен"
  else
    echo "$active"
fi