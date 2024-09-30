#!/usr/bin/bash

#Serash youtube

input=$(yad \
 --title="" \
 --text="Please enter your details:" \
 --image="/usr/share/icons/Tango/scalable/emotes/face-smile.svg" \
 --form \
 --field="Search your track or playlist URL " \
 --fixed \
 --width=400 \
 --height=100 \
 --separator="\t")
 
if [[ $input =~ "https" ]]
then
   echo "playlist"
else
   echo "track"
fi