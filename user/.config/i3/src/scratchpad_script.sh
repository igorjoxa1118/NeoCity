#!/usr/bin/env bash

# File:           scratchpad_script.sh
# Description:    Script to toggle or create scratchpad windows
# Author:       RayZ0rr, Reinaldo Molina
# Revision:     0.0.0
# Created:        Fri Jan 18 2019 12:20
# Last Modified:  Fri Feb 12 2022

############# GLOBVAR/PREP ###############

name="$1"
Usage="\
  Usage: $(basename $0) <name> <command>
  <name>    : name the window has
  <command> : command used to launch window in case doesnt exist
  E.g.:  $(basename $0) terminal \"$TERMINAL --title=terminal\"
  "

# Terminal width and position variables ( you may use these but currently not used in script )
# host=`hostname`
# width=1920
# height=440
# posy=32
# if [ "$host" = "predator" ]; then
#   width=3840
#   height=800
#   posy=48
# fi

############## USGCHECKS #################

if [[ $# -lt 1 || "$1" =~ ^(-h|--help)$ || $# -gt 2 ]]; then
  echo "$Usage"
  exit 1
fi

################ MAIN ####################

visible_wid="$(xdotool search --onlyvisible --classname "${name}" | tail -1 2> /dev/null)"

if [[ -z "$visible_wid" ]]; then # If the scratchpad window is not visible
  wid="$(xdotool search --classname "${name}" | tail -1 2> /dev/null)"
  if [[ -z "$wid" ]]; then       # If the scratchpad window does not exist
    if [[ $# -ne 2 ]]; then    # If a command to launch it was not provided
      echo "${name} not found. A command was not provided to launch it."
      exit 2
    fi

    echo "${name} not found. Executing: '${@: 2}'."
    if ! eval "${@: 2}" ; then
      echo "Provided command '${@: 2}' failed"
      exit $?
    fi
    eval "${@: 2}"

    # Wait for application to be available
    while [[ -z "$wid" ]]; do
      sleep 0.05;
      wid="$(xdotool search --classname "${name}" | tail -1 2> /dev/null)"
    done

    i3-msg "[instance=\"${name}\"] scratchpad show; \
      [instance=\"${name}\"] move position center"
    exit 0
  fi

  echo "${name} found. Showing scratchpad."
  i3-msg "[instance=\"${name}\"] scratchpad show; \
    [instance=\"${name}\"] move position center"
  exit $?
fi

echo "Hiding instance of ${name}."
i3-msg "[instance=\"${name}\"] scratchpad show"
exit $?