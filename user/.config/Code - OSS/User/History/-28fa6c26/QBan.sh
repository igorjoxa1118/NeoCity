#!/bin/bash

#set -x 

yad \
 --image="./icons/backup.svg" \
  --geometry=20x40+500+400 \
  --fontname="Iosevka Term Regular 12" \
  --wrap \
  --justify="center" \
  --margins=1 \
  --tail \
  --editable \
  --fore="#bb9af7" \
  --back="#16161E" \
  --listen \
  --auto-close \
  --auto-kill \
  --monitor \
  --text-info &