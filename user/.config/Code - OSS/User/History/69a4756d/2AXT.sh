#!/usr/bin/bash

#Serash youtube
# mpv ytdl://ytsearch:'Cyberpunk Ambiant' --no-video -ao=pulse --term-playing-msg='Title: ${media-title}'
mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "https://www.youtube.com/playlist?list=PLQQ-A7Ds57kTCJ750usNrWbP2rt4SIpfy"