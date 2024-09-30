#!/usr/bin/bash

if [ -z $(sudo systemctl status smb | grep '(running)' | awk '{print $3}') == '(running)' ]; then
  echo "Сервез активен и запущен"
  else
    echo "Что-то не так"
fi