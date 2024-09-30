#!/usr/bin/bash

#Serash youtube

music=$(yad \
    --entry \
    --text "Enter value" \
    --entry-text="Serach you music" \
    --button=Search \
    --width=400 \
    --height=100 \
    --fixed \
    --center)

mpv ytdl://ytsearch:"$music" --no-video -ao=pulse --term-playing-msg='Title: ${media-title}'
#mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "https://www.youtube.com/watch?v=mbogNjIjRSU&list=PL7QCLi1yaGeeoKb0u6c9Cc23Mw4NYpPs2"