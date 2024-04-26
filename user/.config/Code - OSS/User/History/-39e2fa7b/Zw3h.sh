#!/usr/bin/bash

#{1..$(echo $(<"/home/vir0id/log_play_info") | wc -l ~/log_play_info | awk '{print $1}')}
#Serash youtube

log_play_info="$HOME/log_play_info"

function info_playlist() {
 mpv --fs -ao=pulse --no-video --shuffle --script-opts-append=osc-visibility=always --term-playing-msg='Title: ${media-title}' "$input" 2>&1 | yad \
 --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
 --geometry=20x40+500+400 \
 --fontname="Iosevka Term Regular 12" \
 --wrap --justify="center" \
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
}

function info_track() {
 mpv --fs ytdl://ytsearch:"$input" --no-video -ao=pulse --script-opts-append=osc-visibility=always --term-playing-msg='Title: ${media-title}' 2>&1 | yad \
 --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
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
}

function mpv_audio() {

function close_exit() {
   killall mpv
   killall yad
}

export -f close_exit
export -f info_playlist
export -f info_track

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
   info_playlist
else
   info_track
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
export -f info_playlist
export -f info_track

endoff=$(yad \
   --title="Search-tube" \
   --text="What are you want?" \
   --image="$HOME/.config/i3/scripts/polybar-mpv/icons/youtube.svg" \
   --text-align=center \
   --fixed \
   --width=280 \
   --height=100 \
   --button-align=center \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/window-close.svg!Exit:bash -c close_exit_sec" \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/go-down-skip.svg!Close:bash -c close" \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/audio-volume-medium.svg!Audio:bash -c mpv_audio" \
   --button="!$HOME/.config/i3/scripts/polybar-mpv/icons/filmgrain.svg!Video:bash -c mpv_video" \
   --separator="\t")

