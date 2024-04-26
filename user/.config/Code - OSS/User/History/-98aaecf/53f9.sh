#!/bin/sh

# First we append the saved layout of workspace N to workspace M
i3-msg "workspace --no-auto-back-and-forth M; append_layout ~/.config/i3/workspace_N.json"

# And finally we fill the containers with the programs they had
(xfce4-terminal &)
(xfce4-terminal &)
(xfce4-terminal &)