#!/usr/bin/bash

#mpv -ao=pulse --no-video --shuffle --term-playing-msg='Title: ${media-title}' "https://www.youtube.com/playlist?list=PLQQ-A7Ds57kTCJ750usNrWbP2rt4SIpfy"

if [[ "x$1" == "x" ]]; then
  echo "Usage: mpvy <URL>"
else
  title=`youtube-dl --skip-download --get-title $1`
  mpv --no-video --term-playing-msg "### $title ###" $1
fi