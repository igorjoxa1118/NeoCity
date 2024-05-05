#!/usr/bin/env bash

read -r RICETHEME < "$HOME"/.config/i3/.rice
export RICETHEME
PATH="$HOME/.config/i3/scripts:$PATH"
rice_dir="$HOME/.config/i3/rices/$RICETHEME"
export XDG_CURRENT_DESKTOP='i3'