#!/usr/bin/bash

#Serash youtube
# mpv ytdl://ytsearch:'Cyberpunk Ambiant' --no-video -ao=pulse --term-playing-msg='Title: ${media-title}'
mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "https://www.youtube.com/watch?v=mbogNjIjRSU&list=PL7QCLi1yaGeeoKb0u6c9Cc23Mw4NYpPs2"