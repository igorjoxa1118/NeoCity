#!/bin/sh
i3-save-tree --workspace 7 > ~/test_term/workspace_N.json
sed -i 's|^\(\s*\)// "|\1"|g; /^\s*\/\//d' ~/test_term/workspace_N.json
# First we append the saved layout of workspace N to workspace M
i3-msg "workspace --no-auto-back-and-forth M; append_layout ~/test_term/workspace_N.json"

# And finally we fill the containers with the programs they had
#(xfce4-terminal -x cmus &)
#(xfce4-terminal  &)
#(xfce4-terminal  &)
#(xfce4-terminal  &) 

## Зависимости perl-anyevent-i3 и autotiling