#!/usr/bin/bash

#Serash youtube

OPTIONS=(1 "Синхронизировать домашний каталог"
         2 "Создать резервную копию root+home"
         3 "Удалить резервные копии"
         4 "Создать архив sys.tar.gz"
         5 "Записать архив sys.tar.gz в Drive"
         6 "Извлечь архив в /"
         7 "Установка программного обеспечения")


CHOICE=$(yad \
    --entry \
    --text "Enter value" \
    --entry-text="Search yout music" \
    --button=Search \
    --width=400 \
    --height=100 \
    --fixed \
    --center
    "${OPTIONS[@]}")

case $CHOICE in

1)

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

2)

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
#mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "https://www.youtube.com/watch?v=mbogNjIjRSU&list=PL7QCLi1yaGeeoKb0u6c9Cc23Mw4NYpPs2"