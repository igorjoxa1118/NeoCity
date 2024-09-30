#!/usr/bin/bash

#Serash youtube

OPTIONS=(1 "Найти трэк"
         2 "Загрузить плейлист")

case $CHOICE in
"1" )

track=$(yad \
    --entry \
    --text "Enter value" \
    --entry-text="Serach you music" \
    --button=Search \
    --width=400 \
    --height=100 \
    --fixed \
    --center)

mpv ytdl://ytsearch:"$track" --no-video -ao=pulse --term-playing-msg='Title: ${media-title}'

;;

"2" )

playlist=$(yad \
    --entry \
    --text "Enter value" \
    --entry-text="Serach you music" \
    --button=Search \
    --width=400 \
    --height=100 \
    --fixed \
    --center)

mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "$playlist"

;;

esac