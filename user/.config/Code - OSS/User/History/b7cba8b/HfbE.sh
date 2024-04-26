#!/usr/bin/bash

#Serash youtube

function mpv_audio() {

function close_exit() {
   killall mpv
   killall yad
}

export -f close_exit

input=$(yad \
 --title="Search-tube" \
 --text="Press Enter:" \
 --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
 --icon-size=48 \
 --form \
 --field="  Your track or playlist URL:  " \
 --button="Exit:bash -c close_exit" \
 --fixed \
 --width=800 \
 --height=100 \
 --separator="\t")
 
if [[ $input =~ "https" ]]; then
   mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "$input"
else
   mpv ytdl://ytsearch:"$input" --no-video -ao=pulse --term-playing-msg='Title: ${media-title}'
fi

}

function mpv_video() {

function close_exit() {
   killall mpv
   killall yad
}

export -f close_exit

input=$(yad \
 --title="Search-tube" \
 --text="Press Enter:" \
 --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
 --icon-size=48 \
 --form \
 --field="  Your video or playlist URL:  " \
 --button="Exit:bash -c close_exit" \
 --fixed \
 --width=800 \
 --height=100 \
 --separator="\t")
 
if [[ $input =~ "https" ]]; then
   mpv -ao=pulse --shuffle --term-playing-msg='Title: ${media-title}' "$input"
else
   mpv ytdl://ytsearch:"$input" -ao=pulse --term-playing-msg='Title: ${media-title}'
fi

}

function close_exit_sec() {
   killall mpv
   killall yad
}

function close() {
   killall yad
}

export -f mpv_audio
export -f mpv_video
export -f close_exit_sec
export -f close

endoff=$(yad \
   --title="Search-tube" \
   --text="What are you want?" \
   --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
   --text-align=center \
   --fixed \
   --width=280 \
   --height=100 \
   --button-align=center \
   --button="Exit:bash -c close_exit_sec" \
   --button="Close:bash -c close" \
   --button="Audio:bash -c mpv_audio" \
   --button="Video:bash -c mpv_video" \
   --separator="\t")
